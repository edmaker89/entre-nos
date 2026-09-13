import hashlib

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from app.api.auth import CurrentUser, DB, issue_session
from app.config import settings
from app.db.models import Audit, Family, FamilyInvite, Membership, User, now
from app.db.unit_of_work import family_context
from app.domain.passwords import hash_password, validate_new_password
from app.domain.rate_limits import consume
from app.errors import AppError


router = APIRouter(prefix="/api/v1/auth/invites", tags=["invite-auth"])


class InviteToken(BaseModel):
    token: str = Field(min_length=3, max_length=500)


class InviteRegistration(InviteToken):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=200)

    @field_validator("name")
    @classmethod
    def meaningful_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Informe seu nome.")
        return value

    @field_validator("email")
    @classmethod
    def recognizable_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Informe um email válido.")
        return value


def _invalid_invite():
    return AppError(
        "invalid_invite",
        "Este convite expirou ou não está mais disponível. Peça um novo convite.",
        410,
    )


def _parse(token: str) -> tuple[str, str]:
    try:
        family_id, secret = token.split(".", 1)
    except ValueError:
        raise _invalid_invite() from None
    if not family_id or not secret:
        raise _invalid_invite()
    return family_id, hashlib.sha256(secret.encode()).hexdigest()


def _load_invite(db: DB, token: str, *, lock: bool) -> tuple[Family, FamilyInvite]:
    family_id, token_hash = _parse(token)
    try:
        family_context(db, family_id, lock=lock)
    except AppError:
        raise _invalid_invite() from None
    statement = select(FamilyInvite).where(
        FamilyInvite.family_id == family_id,
        FamilyInvite.token_hash == token_hash,
    )
    if lock:
        statement = statement.with_for_update()
    invite = db.scalar(statement)
    if (
        invite is None
        or invite.used_at is not None
        or invite.revoked_at is not None
        or invite.expires_at <= now()
    ):
        raise _invalid_invite()
    family = db.get(Family, family_id)
    return family, invite


def _limit_public(db: DB, request: Request):
    allowed = consume(
        db,
        "invite_origin",
        request.client.host if request.client else "unknown",
        60,
        3600,
        settings.auth_rate_limit_secret,
    )
    if not allowed:
        raise AppError("rate_limit", "Muitas tentativas. Aguarde antes de tentar novamente.", 429)


@router.post("/inspect")
def inspect_invite(body: InviteToken, request: Request, db: DB):
    _limit_public(db, request)
    family, invite = _load_invite(db, body.token, lock=False)
    return {
        "status": "valid",
        "family_name": family.name,
        "expires_at": invite.expires_at.isoformat(),
    }


@router.post("/accept")
def accept_invite(body: InviteToken, db: DB, user: CurrentUser):
    family, invite = _load_invite(db, body.token, lock=True)
    memberships = db.scalars(select(Membership).where(Membership.user_id == user.id)).all()
    if any(membership.family_id != family.id for membership in memberships):
        raise AppError(
            "family_conflict",
            "Esta versão aceita uma única família por usuário.",
            409,
        )
    if memberships:
        raise AppError("already_member", "Você já participa desta família.", 409)
    db.add(Membership(family_id=family.id, user_id=user.id, role="member"))
    invite.used_at = now()
    invite.used_by = user.id
    invite.version += 1
    db.add(
        Audit(
            family_id=family.id,
            actor_id=user.id,
            operation="family.invite.accept",
            entity_id=invite.id,
            details={"fields": ["used_at", "used_by"]},
        )
    )
    return {"status": "accepted", "family_id": family.id}


@router.post("/register")
def register_with_invite(
    body: InviteRegistration,
    response: Response,
    request: Request,
    db: DB,
):
    _limit_public(db, request)
    try:
        password = validate_new_password(body.password)
    except ValueError as error:
        raise AppError("invalid_password", str(error), 422, fields=["body.password"]) from None
    email = str(body.email).strip().lower()
    if db.scalar(select(User.id).where(User.email == email)) is not None:
        raise AppError("email_exists", "Este email já possui uma conta.", 409)
    family, invite = _load_invite(db, body.token, lock=True)
    user = User(name=body.name, email=email, password_hash=hash_password(password))
    db.add(user)
    db.flush()
    db.add(Membership(family_id=family.id, user_id=user.id, role="member"))
    invite.used_at = now()
    invite.used_by = user.id
    invite.version += 1
    db.add(
        Audit(
            family_id=family.id,
            actor_id=user.id,
            operation="family.invite.register",
            entity_id=invite.id,
            details={"fields": ["used_at", "used_by"]},
        )
    )
    csrf = issue_session(db, response, user)
    response.status_code = 201
    return {
        "user": {"id": user.id, "name": user.name},
        "family_id": family.id,
        "csrf_token": csrf,
    }
