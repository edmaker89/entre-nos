from datetime import date
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from app.api.auth import DB, FamilyID
from app.api.common import get_row, serialize, operation, reopen_month
from app.api.commitments import ensure_cycle
from app.db.models import Cycle, Card, Commitment, Installment, Advance
from app.db.unit_of_work import check_version
from app.domain.cycles import cycle_for_month, add_months, month_start
from app.errors import AppError

router = APIRouter(prefix="/api/v1", tags=["cycles"])


class Version(BaseModel):
    version: int = Field(ge=1)


class Closing(Version):
    closing_date: date


def effective_first(db, card, purchased, override=None):
    known = {
        c.month: c.closing_date for c in db.scalars(select(Cycle).where(Cycle.card_id == card.id))
    }
    if override:
        known[override[0]] = override[1]
    for offset in range(4):
        month = add_months(month_start(purchased), offset)
        default = cycle_for_month(month, card.closing_day, card.due_day)
        closing = known.get(month, default["closing_date"])
        if purchased <= closing:
            return month, purchased == closing
    raise AppError("invalid_cycle", "Não foi possível determinar o ciclo.", 422)


def closing_changes(db, id, body):
    cycle = get_row(db, Cycle, id)
    if cycle.version != body.version or cycle.paid_at:
        raise AppError("cycle_conflict", "Recarregue ou reabra a fatura antes de alterar.")
    card = get_row(db, Card, cycle.card_id)
    previous = db.scalar(
        select(Cycle)
        .where(Cycle.card_id == card.id, Cycle.month < cycle.month)
        .order_by(Cycle.month.desc())
    )
    following = db.scalar(
        select(Cycle)
        .where(Cycle.card_id == card.id, Cycle.month > cycle.month)
        .order_by(Cycle.month)
    )
    if (
        body.closing_date >= cycle.due_date
        or (previous and body.closing_date <= previous.closing_date)
        or (following and body.closing_date >= following.closing_date)
    ):
        raise AppError(
            "invalid_closing",
            "Fechamento deve preservar a ordem dos ciclos e preceder o vencimento.",
        )
    changes = []
    for c in db.scalars(
        select(Commitment).where(Commitment.card_id == card.id, Commitment.deleted_at.is_(None))
    ):
        parts = db.scalars(
            select(Installment)
            .where(Installment.commitment_id == c.id, Installment.deleted_at.is_(None))
            .order_by(Installment.number)
        ).all()
        if not parts or any(p.paid_at or p.manually_assigned for p in parts):
            continue
        if any(p.cycle_id and db.get(Cycle, p.cycle_id).confirmed for p in parts):
            continue
        if db.scalar(
            select(Advance.id).where(Advance.commitment_id == c.id, Advance.state != "cancelled")
        ):
            continue
        first, review = effective_first(db, card, c.purchased_at, (cycle.month, body.closing_date))
        if parts[0].month != first:
            changes.append({"commitment_id": c.id, "first_month": first.isoformat()})
    return cycle, card, changes


@router.get("/cards/{id}/cycles")
def listing(id: str, db: DB, family: FamilyID):
    get_row(db, Card, id)
    return [
        serialize(c)
        for c in db.scalars(select(Cycle).where(Cycle.card_id == id).order_by(Cycle.month))
    ]


@router.post("/cycles/{id}/preview-close")
def preview(id: str, body: Closing, db: DB, family: FamilyID):
    cycle, card, changes = closing_changes(db, id, body)
    return {"changes": changes}


@router.patch("/cycles/{id}/close")
def close(id: str, body: Closing, request: Request, db: DB, family: FamilyID):
    def action():
        cycle, card, changes = closing_changes(db, id, body)
        check_version(cycle, body.version)
        cycle.closing_date = body.closing_date
        cycle.confirmed = False
        for change in changes:
            c = db.get(Commitment, change["commitment_id"])
            c.version += 1
            parts = db.scalars(
                select(Installment)
                .where(Installment.commitment_id == c.id)
                .order_by(Installment.number)
            ).all()
            first = date.fromisoformat(change["first_month"])
            for index, part in enumerate(parts):
                target = ensure_cycle(db, family, card, add_months(first, index))
                part.month = target.month
                part.due_date = target.due_date
                part.cycle_id = target.id
                part.version += 1
                target.confirmed = False
                target.version += 1
                reopen_month(db, family, target.month)
        db.flush()
        return {**serialize(cycle), "changes": changes}

    return operation(db, family, request, body.model_dump(), action)


@router.post("/cycles/{id}/confirm")
def confirm(id: str, body: Version, request: Request, db: DB, family: FamilyID):
    def action():
        cycle = get_row(db, Cycle, id)
        check_version(cycle, body.version)
        cycle.confirmed = True
        for part in db.scalars(select(Installment).where(Installment.cycle_id == id)):
            part.needs_review = False
        db.flush()
        return serialize(cycle)

    return operation(db, family, request, body.model_dump(), action)
