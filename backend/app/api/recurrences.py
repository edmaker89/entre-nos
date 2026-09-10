from datetime import date
from fastapi import APIRouter, Request, Query
from pydantic import BaseModel, Field, ConfigDict, model_validator
from sqlalchemy import select
from app.api.auth import DB, FamilyID
from app.api.common import get_row, serialize, operation, member, reopen_month
from app.api.commitments import ShareInput
from app.db.models import Recurrence, Occurrence, now
from app.db.unit_of_work import check_version, family_context
from app.domain.cycles import month_start, add_months, on_day
from app.domain.money import MAX_CENTS
from app.errors import AppError

router = APIRouter(prefix="/api/v1", tags=["recurrences"])


class RuleInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    description: str = Field(min_length=1, max_length=200)
    amount_cents: int = Field(gt=0, le=MAX_CENTS)
    variable: bool = False
    due_day: int = Field(ge=1, le=31)
    start_month: date
    shares: list[ShareInput] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def valid(self):
        if sum(s.weight for s in self.shares) <= 0 or len({s.user_id for s in self.shares}) != len(
            self.shares
        ):
            raise ValueError("Divisão inválida.")
        return self


class AmountEdit(BaseModel):
    version: int = Field(ge=1)
    amount_cents: int = Field(gt=0, le=MAX_CENTS)


class End(BaseModel):
    version: int = Field(ge=1)
    end_month: date


def materialize(db, family, start, count):
    family_context(db, family)
    for rule in db.scalars(select(Recurrence).where(Recurrence.deleted_at.is_(None))):
        for index in range(count):
            month = add_months(month_start(start), index)
            if month < rule.start_month or (rule.end_month and month >= rule.end_month):
                continue
            old = db.scalar(
                select(Occurrence).where(
                    Occurrence.recurrence_id == rule.id, Occurrence.month == month
                )
            )
            if old:
                continue
            # Latest confirmed occurrence before this month, never a later value.
            latest = db.scalar(
                select(Occurrence)
                .where(
                    Occurrence.recurrence_id == rule.id,
                    Occurrence.month < month,
                    Occurrence.estimated.is_(False),
                    Occurrence.deleted_at.is_(None),
                )
                .order_by(Occurrence.month.desc())
            )
            amount = latest.amount_cents if rule.variable and latest else rule.amount_cents
            db.add(
                Occurrence(
                    family_id=family,
                    recurrence_id=rule.id,
                    month=month,
                    due_date=on_day(month, rule.due_day),
                    amount_cents=amount,
                    estimated=rule.variable,
                )
            )
            reopen_month(db, family, month)
    db.flush()


@router.post("/recurrences")
def create(body: RuleInput, request: Request, db: DB, family: FamilyID):
    def action():
        for share in body.shares:
            member(db, family, share.user_id)
        data = body.model_dump()
        data["start_month"] = month_start(body.start_month)
        row = Recurrence(family_id=family, **data)
        db.add(row)
        db.flush()
        reopen_month(db, family, row.start_month)
        return serialize(row)

    return operation(db, family, request, body.model_dump(), action)


@router.get("/recurrences")
def listing(
    db: DB,
    family: FamilyID,
    from_month: date = date(2026, 10, 1),
    months: int = Query(default=12, ge=1, le=12),
):
    materialize(db, family, from_month, months)
    end = add_months(month_start(from_month), months)
    return [
        {
            **serialize(r),
            "occurrences": [
                serialize(o)
                for o in db.scalars(
                    select(Occurrence)
                    .where(
                        Occurrence.recurrence_id == r.id,
                        Occurrence.month >= month_start(from_month),
                        Occurrence.month < end,
                        Occurrence.deleted_at.is_(None),
                    )
                    .order_by(Occurrence.month)
                )
            ],
        }
        for r in db.scalars(select(Recurrence).where(Recurrence.deleted_at.is_(None)))
    ]


@router.patch("/occurrences/{id}")
def edit(id: str, body: AmountEdit, request: Request, db: DB, family: FamilyID):
    def action():
        row = get_row(db, Occurrence, id)
        if row.paid_at:
            raise AppError("paid", "Reabra a conta antes de alterar.")
        check_version(row, body.version)
        row.amount_cents = body.amount_cents
        row.estimated = False
        rule = get_row(db, Recurrence, row.recurrence_id)
        if rule.variable:
            next_confirmed = db.scalar(
                select(Occurrence.month)
                .where(
                    Occurrence.recurrence_id == rule.id,
                    Occurrence.month > row.month,
                    Occurrence.estimated.is_(False),
                    Occurrence.deleted_at.is_(None),
                )
                .order_by(Occurrence.month)
                .limit(1)
            )
            for future in db.scalars(
                select(Occurrence).where(
                    Occurrence.recurrence_id == rule.id,
                    Occurrence.month > row.month,
                    Occurrence.estimated.is_(True),
                    Occurrence.paid_at.is_(None),
                    Occurrence.deleted_at.is_(None),
                )
            ):
                if next_confirmed and future.month >= next_confirmed:
                    continue
                future.amount_cents = body.amount_cents
                future.version += 1
        db.flush()
        return serialize(row)

    return operation(db, family, request, body.model_dump(), action)


@router.post("/recurrences/{id}/end")
def end(id: str, body: End, request: Request, db: DB, family: FamilyID):
    def action():
        rule = get_row(db, Recurrence, id)
        check_version(rule, body.version)
        month = month_start(body.end_month)
        rows = db.scalars(
            select(Occurrence).where(
                Occurrence.recurrence_id == id,
                Occurrence.month >= month,
                Occurrence.deleted_at.is_(None),
            )
        ).all()
        if any(o.paid_at for o in rows):
            raise AppError("paid", "Reabra as contas pagas antes de encerrar neste mês.")
        rule.end_month = month
        for row in rows:
            row.deleted_at = now()
        db.flush()
        return serialize(rule)

    return operation(db, family, request, body.model_dump(), action)
