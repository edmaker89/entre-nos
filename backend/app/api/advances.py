from datetime import date
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from app.api.auth import DB, FamilyID
from app.api.common import get_row, serialize, operation, reopen_month
from app.api.commitments import ensure_cycle
from app.db.models import Commitment, Installment, Advance, AdvanceItem, Card, Cycle
from app.db.unit_of_work import check_version
from app.domain.cycles import month_start
from app.domain.money import allocate, MAX_CENTS
from app.errors import AppError

router = APIRouter(prefix="/api/v1/advances", tags=["advances"])


class AdvanceInput(BaseModel):
    commitment_id: str
    version: int = Field(ge=1)
    installment_ids: list[str] = Field(min_length=1, max_length=120)
    planned_date: date
    amount_cents: int = Field(gt=0, le=MAX_CENTS)


def prepare(db, family, body):
    c = get_row(db, Commitment, body.commitment_id)
    if c.version != body.version:
        raise AppError("version_conflict", "Registro alterado. Recarregue.")
    if len(set(body.installment_ids)) != len(body.installment_ids):
        raise AppError("invalid_selection", "Parcela repetida.", 422)
    parts = [get_row(db, Installment, id) for id in body.installment_ids]
    parts.sort(key=lambda p: p.number)
    target = month_start(body.planned_date)
    for p in parts:
        if p.commitment_id != c.id:
            raise AppError("invalid_selection", "Escolha parcelas do mesmo contrato.", 422)
        if p.paid_at:
            raise AppError("paid", "Parcela já paga.")
        if db.scalar(
            select(AdvanceItem.id)
            .join(Advance, Advance.id == AdvanceItem.advance_id)
            .where(AdvanceItem.installment_id == p.id, Advance.state != "cancelled")
        ):
            raise AppError("active_advance", "Parcela já possui antecipação ativa.")
        if target > p.original_month or (
            target == p.original_month and body.planned_date >= p.original_due
        ):
            raise AppError(
                "invalid_date", "A antecipação deve preceder o vencimento original.", 422
            )
    total = sum(p.original_cents for p in parts)
    if not len(parts) <= body.amount_cents <= total:
        raise AppError(
            "invalid_amount", "Valor final deve ser positivo e não superar o original.", 422
        )
    amounts = allocate(body.amount_cents, [p.original_cents for p in parts])
    if min(amounts) < 1:
        raise AppError("invalid_amount", "Cada parcela precisa manter ao menos um centavo.", 422)
    if c.card_id:
        cycle = db.scalar(select(Cycle).where(Cycle.card_id == c.card_id, Cycle.month == target))
        if cycle and cycle.paid_at:
            raise AppError("paid_cycle", "Reabra a fatura de destino.")
    return c, parts, amounts, target, total


@router.post("/preview")
def preview(body: AdvanceInput, db: DB, family: FamilyID):
    c, parts, amounts, target, total = prepare(db, family, body)
    return {
        "month": target.isoformat(),
        "original_cents": total,
        "amount_cents": body.amount_cents,
        "discount_cents": total - body.amount_cents,
        "installments": [
            {
                "id": p.id,
                "number": p.number,
                "amount_cents": amount,
                "original_month": p.original_month.isoformat(),
            }
            for p, amount in zip(parts, amounts)
        ],
    }


@router.post("")
def create(body: AdvanceInput, request: Request, db: DB, family: FamilyID):
    def action():
        c, parts, amounts, target, total = prepare(db, family, body)
        check_version(c, body.version)
        card = get_row(db, Card, c.card_id) if c.card_id else None
        cycle = ensure_cycle(db, family, card, target) if card else None
        plan = Advance(
            family_id=family,
            commitment_id=c.id,
            month=target,
            planned_date=body.planned_date,
            amount_cents=body.amount_cents,
        )
        db.add(plan)
        db.flush()
        for p, amount in zip(parts, amounts):
            db.add(
                AdvanceItem(
                    family_id=family,
                    advance_id=plan.id,
                    installment_id=p.id,
                    snapshot={
                        "month": p.month.isoformat(),
                        "due_date": p.due_date.isoformat(),
                        "amount_cents": p.amount_cents,
                        "cycle_id": p.cycle_id,
                        "needs_review": p.needs_review,
                        "manually_assigned": p.manually_assigned,
                    },
                )
            )
            p.month = target
            p.due_date = cycle.due_date if cycle else body.planned_date
            p.amount_cents = amount
            p.cycle_id = cycle.id if cycle else None
            p.version += 1
        if cycle:
            cycle.confirmed = False
            cycle.version += 1
        reopen_month(db, family, target)
        db.flush()
        return serialize(plan)

    return operation(db, family, request, body.model_dump(), action)


@router.get("")
def listing(db: DB, family: FamilyID):
    return [
        {
            **serialize(a),
            "items": [
                serialize(i)
                for i in db.scalars(select(AdvanceItem).where(AdvanceItem.advance_id == a.id))
            ],
        }
        for a in db.scalars(select(Advance).order_by(Advance.created_at.desc()))
    ]
