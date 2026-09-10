from datetime import date, datetime
from sqlalchemy import inspect, select
from app.db.models import Membership, MonthClosure
from app.db.unit_of_work import mutate
from app.errors import AppError


def serialize(row):
    result = {}
    for column in inspect(row).mapper.column_attrs:
        value = getattr(row, column.key)
        result[column.key] = value.isoformat() if isinstance(value, (date, datetime)) else value
    return result


def get_row(db, model, id):
    row = db.get(model, id)
    if row is None or getattr(row, "deleted_at", None):
        raise AppError("not_found", "Registro não encontrado.", 404)
    return row


def member(db, family, user):
    if db.get(Membership, (family, user)) is None:
        raise AppError("invalid_member", "Responsável não pertence à família.", 422)


def operation(db, family, request, payload, action):
    return mutate(
        db,
        family,
        request.headers.get("idempotency-key"),
        {"path": request.url.path, "method": request.method, "body": payload},
        action,
    )


def reopen_month(db, family, month):
    closure = db.scalar(
        select(MonthClosure).where(MonthClosure.family_id == family, MonthClosure.month == month)
    )
    if closure:
        closure.closed = False
        closure.version += 1
