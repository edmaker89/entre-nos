from datetime import date
from fastapi import APIRouter, Request
from sqlalchemy import select
from app.api.auth import DB, FamilyID
from app.api.common import get_row, serialize, operation, reopen_month
from app.api.payments import PaymentInput
from app.db.models import Advance, AdvanceItem, Installment, Commitment, Cycle
from app.db.unit_of_work import check_version
from app.errors import AppError

router = APIRouter(prefix="/api/v1/advances", tags=["advances"])


@router.post("/{id}/{action}")
def change(id: str, action: str, body: PaymentInput, request: Request, db: DB, family: FamilyID):
    def apply():
        plan = get_row(db, Advance, id)
        if action not in ("pay", "reopen", "cancel"):
            raise AppError("not_found", "Operação não encontrada.", 404)
        if plan.state == "cancelled":
            raise AppError("cancelled", "Antecipação já cancelada.")
        c = get_row(db, Commitment, plan.commitment_id)
        items = db.scalars(select(AdvanceItem).where(AdvanceItem.advance_id == id)).all()
        parts = [get_row(db, Installment, i.installment_id) for i in items]
        if action != "cancel" and c.card_id:
            raise AppError("invoice_required", "Pague ou reabra a fatura de destino.")
        if action == "cancel":
            if any(p.paid_at for p in parts):
                raise AppError("paid", "Reabra o pagamento antes de cancelar.")
            for item in items:
                cycle_id = item.snapshot["cycle_id"]
                if cycle_id and get_row(db, Cycle, cycle_id).paid_at:
                    raise AppError("paid_cycle", "Reabra a fatura original antes de restaurar.")
        if action == "pay" and not body.paid_at:
            raise AppError("validation", "Informe a data do pagamento.", 422)
        check_version(plan, body.version)
        c.version += 1
        for item, part in zip(items, parts):
            if action == "cancel":
                for key, value in item.snapshot.items():
                    setattr(
                        part,
                        key,
                        date.fromisoformat(value) if key in ("month", "due_date") else value,
                    )
                if part.cycle_id:
                    db.get(Cycle, part.cycle_id).confirmed = False
                reopen_month(db, family, part.month)
            else:
                part.paid_at = body.paid_at if action == "pay" else None
                part.payment_kind = "advance" if action == "pay" else None
                if action == "reopen":
                    reopen_month(db, family, part.month)
            part.version += 1
        plan.state = {"pay": "paid", "reopen": "planned", "cancel": "cancelled"}[action]
        db.flush()
        return serialize(plan)

    return operation(db, family, request, body.model_dump(), apply)
