from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Membership, User
from app.db.unit_of_work import family_context
from app.errors import AppError


def resolve_family(request: Request, db: Session, user: User) -> str:
    memberships = db.scalars(
        select(Membership).where(Membership.user_id == user.id).order_by(Membership.family_id)
    ).all()
    if not memberships:
        raise AppError("family_required", "Entre em uma família para continuar.", 403)
    if len(memberships) != 1:
        raise AppError(
            "multiple_families",
            "Esta versão aceita uma única família por usuário.",
            409,
        )
    resolved = memberships[0].family_id
    family_context(db, resolved, lock=request.method not in ("GET", "HEAD", "OPTIONS"))
    request.state.family_id = resolved
    return resolved
