from datetime import date
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, ConfigDict, model_validator
from sqlalchemy import select
from app.api.auth import DB, FamilyID
from app.api.common import get_row, serialize, member, operation, reopen_month
from app.db.models import Card, Cycle, Commitment, Installment, Share
from app.domain.cycles import first_cycle, cycle_for_month, add_months, month_start
from app.domain.money import installments, MAX_CENTS
from app.errors import AppError

router = APIRouter(prefix="/api/v1/commitments", tags=["commitments"])


class ShareInput(BaseModel):
    user_id: str
    weight: int = Field(ge=0, le=MAX_CENTS)


class PurchaseInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    description: str = Field(min_length=1, max_length=200)
    buyer_id: str
    card_id: str | None = None
    purchased_at: date
    total_cents: int = Field(gt=0, le=MAX_CENTS)
    count: int = Field(ge=1, le=120)
    shares: list[ShareInput] = Field(min_length=1, max_length=20)
    first_month: date | None = None
    category: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def valid(self):
        if self.total_cents < self.count or sum(s.weight for s in self.shares) != self.total_cents:
            raise ValueError(
                "A divisão precisa somar o total e cada parcela deve ter ao menos um centavo."
            )
        if len({s.user_id for s in self.shares}) != len(self.shares):
            raise ValueError("Responsável repetido.")
        return self


def ensure_cycle(db, family, card, month):
    cycle = db.scalar(select(Cycle).where(Cycle.card_id == card.id, Cycle.month == month))
    if not cycle:
        cycle = Cycle(
            family_id=family,
            card_id=card.id,
            **cycle_for_month(month, card.closing_day, card.due_day),
        )
        db.add(cycle)
        db.flush()
    if cycle.paid_at:
        raise AppError("paid_cycle", "Reabra a fatura antes de adicionar parcelas.")
    return cycle


def preview_purchase(db, family, body):
    member(db, family, body.buyer_id)
    for share in body.shares:
        member(db, family, share.user_id)
    card = get_row(db, Card, body.card_id) if body.card_id else None
    if card:
        first = first_cycle(body.purchased_at, card.closing_day, card.due_day)
        # Effective cycle dates supersede habitual dates when present.
        known = db.scalars(
            select(Cycle)
            .where(Cycle.card_id == card.id, Cycle.closing_date >= body.purchased_at)
            .order_by(Cycle.closing_date)
        ).first()
        if known and known.closing_date <= add_months(body.purchased_at, 2):
            first = {
                "month": known.month,
                "due_date": known.due_date,
                "needs_review": known.closing_date == body.purchased_at,
            }
        start = month_start(body.first_month) if body.first_month else first["month"]
    else:
        first = {"needs_review": False}
        start = month_start(body.first_month or body.purchased_at)
    parts = []
    for i, amount in enumerate(installments(body.total_cents, body.count)):
        month = add_months(start, i)
        due = cycle_for_month(month, card.closing_day, card.due_day)["due_date"] if card else month
        parts.append(
            {
                "number": i + 1,
                "amount_cents": amount,
                "month": month.isoformat(),
                "due_date": due.isoformat(),
                "needs_review": first["needs_review"],
            }
        )
    return {"installments": parts, "shares": [s.model_dump() for s in body.shares]}


def details(db, commitment):
    parts = db.scalars(
        select(Installment)
        .where(Installment.commitment_id == commitment.id, Installment.deleted_at.is_(None))
        .order_by(Installment.number)
    ).all()
    shares = db.scalars(
        select(Share).where(Share.commitment_id == commitment.id).order_by(Share.position)
    ).all()
    pending = [p for p in parts if p.paid_at is None]
    return {
        **serialize(commitment),
        "installments": [serialize(p) for p in parts],
        "shares": [serialize(s) for s in shares],
        "pending_count": len(pending),
        "last_open_number": max((p.number for p in pending), default=None),
    }


def persist_purchase(db, family, body, preview, *, imported=False, numbers=None, kind=None):
    c = Commitment(
        family_id=family,
        description=body.description,
        buyer_id=body.buyer_id,
        card_id=body.card_id,
        purchased_at=body.purchased_at,
        total_cents=body.total_cents,
        original_count=body.count,
        imported=imported,
        category=body.category,
        kind=kind or ("purchase" if body.card_id else "expense"),
    )
    db.add(c)
    db.flush()
    for i, share in enumerate(body.shares):
        db.add(
            Share(
                family_id=family,
                commitment_id=c.id,
                user_id=share.user_id,
                weight=share.weight,
                position=i,
            )
        )
    card = get_row(db, Card, body.card_id) if body.card_id else None
    for i, part in enumerate(preview["installments"]):
        month = date.fromisoformat(part["month"])
        cycle = ensure_cycle(db, family, card, month) if card else None
        if cycle:
            cycle.confirmed = False
            cycle.version += 1
        amount = part["amount_cents"]
        due = cycle.due_date if cycle else date.fromisoformat(part["due_date"])
        db.add(
            Installment(
                family_id=family,
                commitment_id=c.id,
                number=numbers[i] if numbers else i + 1,
                original_cents=amount,
                amount_cents=amount,
                original_month=month,
                month=month,
                original_due=due,
                due_date=due,
                cycle_id=cycle.id if cycle else None,
                original_cycle_id=cycle.id if cycle else None,
                needs_review=part["needs_review"],
                manually_assigned=body.first_month is not None,
            )
        )
        reopen_month(db, family, month)
    db.flush()
    return details(db, c)


@router.post("/preview")
def preview(body: PurchaseInput, db: DB, family: FamilyID):
    return preview_purchase(db, family, body)


@router.post("")
def create(body: PurchaseInput, request: Request, db: DB, family: FamilyID):
    return operation(
        db,
        family,
        request,
        body.model_dump(),
        lambda: persist_purchase(db, family, body, preview_purchase(db, family, body)),
    )


@router.get("")
def listing(db: DB, family: FamilyID):
    return [
        serialize(c)
        for c in db.scalars(
            select(Commitment)
            .where(Commitment.deleted_at.is_(None))
            .order_by(Commitment.created_at.desc())
        )
    ]


@router.get("/{id}")
def get(id: str, db: DB, family: FamilyID):
    return details(db, get_row(db, Commitment, id))
