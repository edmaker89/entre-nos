from fastapi import APIRouter, Request
from sqlalchemy import select
from app.api.auth import DB, FamilyID
from app.api.common import operation, serialize
from app.api.months import parse_month, month_data
from app.db.models import MonthClosure
from app.errors import AppError

router = APIRouter(prefix="/api/v1/months", tags=["months"])


@router.post("/{month}/close")
def close(month: str, request: Request, db: DB, family: FamilyID):
    def action():
        target = parse_month(month)
        report = month_data(db, family, target)
        if report["totals"]["remaining"]:
            raise AppError(
                "pending_expenses",
                "Existem despesas pendentes. Registre os pagamentos antes de sinalizar o mês como quitado.",
            )
        row = db.scalar(select(MonthClosure).where(MonthClosure.month == target))
        if not row:
            row = MonthClosure(family_id=family, month=target)
            db.add(row)
        else:
            row.closed = True
            row.version += 1
        db.flush()
        return serialize(row)

    return operation(db, family, request, {}, action)
