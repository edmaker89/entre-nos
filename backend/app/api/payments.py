from datetime import date
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from app.api.auth import DB, FamilyID
from app.api.common import get_row, serialize, operation, reopen_month
from app.db.models import Cycle, Installment, Occurrence, Advance, AdvanceItem, Commitment
from app.db.unit_of_work import check_version
from app.errors import AppError

router = APIRouter(prefix="/api/v1", tags=["payments"])


class PaymentInput(BaseModel):
    version: int = Field(ge=1)
    paid_at: date | None = None


def sync_advances(db, part_ids):
    plans = (
        db.scalars(
            select(Advance)
            .join(AdvanceItem, AdvanceItem.advance_id == Advance.id)
            .where(AdvanceItem.installment_id.in_(part_ids), Advance.state != "cancelled")
        )
        .unique()
        .all()
    )
    for plan in plans:
        ids = db.scalars(
            select(AdvanceItem.installment_id).where(AdvanceItem.advance_id == plan.id)
        ).all()
        parts = db.scalars(select(Installment).where(Installment.id.in_(ids))).all()
        state = "paid" if all(p.paid_at for p in parts) else "planned"
        if state != plan.state:
            plan.state = state
            plan.version += 1


def apply_payment(db, family, kind, id, body, reopen):
    model = {"invoices": Cycle, "installments": Installment, "occurrences": Occurrence}[kind]
    row = get_row(db, model, id)
    if kind == "installments" and row.cycle_id:
        raise AppError("invoice_required", "Pague ou reabra a fatura do cartão.")
    if not reopen and not body.paid_at:
        raise AppError("validation", "Informe a data do pagamento.", 422)
    check_version(row, body.version)
    paid = None if reopen else body.paid_at
    row.paid_at = paid
    if kind == "invoices":
        parts = db.scalars(
            select(Installment).where(Installment.cycle_id == id, Installment.deleted_at.is_(None))
        ).all()
    elif kind == "installments":
        parts = [row]
    else:
        parts = []
    touched = set()
    for part in parts:
        part.paid_at = paid
        if part is not row:
            part.version += 1
        active = db.scalar(
            select(AdvanceItem.id)
            .join(Advance, Advance.id == AdvanceItem.advance_id)
            .where(AdvanceItem.installment_id == part.id, Advance.state != "cancelled")
        )
        part.payment_kind = None if reopen else ("advance" if active else "regular")
        touched.add(part.commitment_id)
    for cid in touched:
        db.get(Commitment, cid).version += 1
    db.flush()
    sync_advances(db, [p.id for p in parts])
    if reopen:
        reopen_month(db, family, row.month)
    db.flush()
    return serialize(row)


@router.post("/invoices/{id}/{action}")
def invoice(id: str, action: str, body: PaymentInput, request: Request, db: DB, family: FamilyID):
    return dispatch(db, family, request, "invoices", id, action, body)


@router.post("/installments/{id}/{action}")
def installment(
    id: str, action: str, body: PaymentInput, request: Request, db: DB, family: FamilyID
):
    return dispatch(db, family, request, "installments", id, action, body)


@router.post("/occurrences/{id}/{action}")
def occurrence(
    id: str, action: str, body: PaymentInput, request: Request, db: DB, family: FamilyID
):
    return dispatch(db, family, request, "occurrences", id, action, body)


def dispatch(db, family, request, kind, id, action, body):
    if action not in ("pay", "reopen"):
        raise AppError("not_found", "Operação não encontrada.", 404)
    return operation(
        db,
        family,
        request,
        body.model_dump(),
        lambda: apply_payment(db, family, kind, id, body, action == "reopen"),
    )
