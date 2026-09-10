from datetime import date
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from app.api.auth import DB, FamilyID
from app.api.common import get_row, operation, reopen_month
from app.api.commitments import details, ensure_cycle
from app.db.models import Commitment, Installment, Advance, Card, now
from app.db.unit_of_work import check_version
from app.domain.cycles import month_start, add_months
from app.errors import AppError

router = APIRouter(prefix="/api/v1/commitments", tags=["changes"])


class Shift(BaseModel):
    version: int = Field(ge=1)
    first_month: date


class Edit(BaseModel):
    version: int = Field(ge=1)
    description: str = Field(min_length=1, max_length=200)


def editable(db, id):
    c = get_row(db, Commitment, id)
    parts = db.scalars(
        select(Installment)
        .where(Installment.commitment_id == id, Installment.deleted_at.is_(None))
        .order_by(Installment.number)
    ).all()
    if any(p.paid_at for p in parts):
        raise AppError("paid", "Reabra os pagamentos antes de alterar a compra.")
    if db.scalar(
        select(Advance.id).where(Advance.commitment_id == id, Advance.state != "cancelled")
    ):
        raise AppError("active_advance", "Cancele a antecipação antes de reorganizar a compra.")
    return c, parts


def shift_preview(db, id, body):
    c, parts = editable(db, id)
    if c.version != body.version:
        raise AppError("version_conflict", "Registro alterado. Recarregue.")
    first = parts[0].month
    target = month_start(body.first_month)
    offset = (target.year - first.year) * 12 + target.month - first.month
    return c, parts, [add_months(p.month, offset) for p in parts], offset


@router.post("/{id}/preview-shift")
def preview(id: str, body: Shift, db: DB, family: FamilyID):
    c, parts, months, offset = shift_preview(db, id, body)
    return {
        "installments": [
            {"number": p.number, "month": m.isoformat(), "amount_cents": p.amount_cents}
            for p, m in zip(parts, months)
        ]
    }


@router.post("/{id}/shift")
def shift(id: str, body: Shift, request: Request, db: DB, family: FamilyID):
    def action():
        c, parts, months, offset = shift_preview(db, id, body)
        check_version(c, body.version)
        card = get_row(db, Card, c.card_id) if c.card_id else None
        for p, m in zip(parts, months):
            cycle = ensure_cycle(db, family, card, m) if card else None
            p.month = m
            p.due_date = cycle.due_date if cycle else add_months(p.due_date, offset)
            p.cycle_id = cycle.id if cycle else None
            p.manually_assigned = True
            p.version += 1
            if cycle:
                cycle.confirmed = False
                cycle.version += 1
            reopen_month(db, family, m)
        db.flush()
        return details(db, c)

    return operation(db, family, request, body.model_dump(), action)


@router.patch("/{id}")
def edit(id: str, body: Edit, request: Request, db: DB, family: FamilyID):
    def action():
        c, parts = editable(db, id)
        check_version(c, body.version)
        if not body.description.strip():
            raise AppError("validation", "Descrição obrigatória.", 422)
        c.description = body.description.strip()
        db.flush()
        return details(db, c)

    return operation(db, family, request, body.model_dump(), action)


@router.delete("/{id}")
def delete(
    id: str, version: int, request: Request, db: DB, family: FamilyID, confirm: bool = False
):
    def action():
        if not confirm:
            raise AppError("confirmation", "Confirme a exclusão da compra e suas parcelas.")
        c, parts = editable(db, id)
        check_version(c, version)
        c.deleted_at = now()
        for part in parts:
            part.deleted_at = c.deleted_at
        return {"ok": True}

    return operation(db, family, request, {"version": version, "confirm": confirm}, action)
