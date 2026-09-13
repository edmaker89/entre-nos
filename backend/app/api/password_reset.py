import hashlib
import logging
import secrets
from datetime import timedelta
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Request, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from app.api.auth import DB
from app.config import settings
from app.db.models import PasswordResetToken, Session as LoginSession, User, now
from app.db.unit_of_work import engine
from app.domain.passwords import hash_password, validate_new_password
from app.domain.rate_limits import consume
from app.email.base import EmailDeliveryError, EmailSender
from app.email.memory import MemoryEmailSender
from app.email.resend import ResendEmailSender
from app.email.templates import password_reset_email
from app.errors import AppError


router = APIRouter(prefix="/api/v1/auth/password-reset", tags=["password-reset"])
logger = logging.getLogger("expense")
GENERIC_RESPONSE = {
    "message": "Se existir uma conta para este email, enviaremos as instruções de redefinição."
}


class ResetRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)

    @field_validator("email")
    @classmethod
    def normalized_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Informe um email válido.")
        return value


class ResetTokenInput(BaseModel):
    token: str = Field(min_length=1, max_length=500)


class ResetComplete(ResetTokenInput):
    password: str = Field(min_length=1, max_length=500)


def _build_email_sender() -> EmailSender:
    if settings.email_provider == "resend" and settings.resend_api_key:
        return ResendEmailSender(
            settings.resend_api_key,
            settings.email_from,
            settings.email_timeout_seconds,
        )
    return MemoryEmailSender()


email_sender = _build_email_sender()


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _invalid_token() -> AppError:
    return AppError(
        "invalid_or_expired_token",
        "Este link expirou ou não está mais disponível. Solicite uma nova redefinição.",
        410,
    )


def _limit_token_origin(db: DB, request: Request) -> None:
    if not consume(
        db,
        "reset_token_origin",
        request.client.host if request.client else "unknown",
        30,
        3600,
        settings.auth_rate_limit_secret,
    ):
        raise AppError("rate_limit", "Muitas tentativas. Aguarde antes de tentar novamente.", 429)


def _load_token(db: DB, raw_token: str, *, lock: bool) -> PasswordResetToken:
    token_hash = _digest(raw_token)
    statement = select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    if lock:
        statement = statement.with_for_update()
    row = db.scalar(statement)
    if (
        row is None
        or not secrets.compare_digest(row.token_hash, token_hash)
        or row.delivery_status != "sent"
        or row.used_at is not None
        or row.revoked_at is not None
        or row.expires_at <= now()
    ):
        raise _invalid_token()
    return row


def _deliver_reset(
    reset_id: str,
    raw_token: str,
    email: str,
    name: str,
    operation_id: str,
) -> None:
    link = f"{settings.public_app_url.rstrip('/')}/reset-password?token={raw_token}"
    status = "sent"
    provider_message_id = None
    try:
        receipt = email_sender.send(
            password_reset_email(email, name, link),
            idempotency_key=f"password-reset/{reset_id}",
        )
        provider_message_id = receipt.message_id
    except EmailDeliveryError:
        status = "failed"
        logger.warning("password_reset_delivery_failed operation_id=%s", operation_id)
    except Exception:
        status = "failed"
        logger.error("password_reset_delivery_failed operation_id=%s", operation_id)

    with Session(engine) as db, db.begin():
        db.execute(text("SET LOCAL ROLE expense_app"))
        row = db.get(PasswordResetToken, reset_id)
        if row is not None:
            row.delivery_status = status
            row.provider_message_id = provider_message_id


@router.post("/request", status_code=202)
def request_reset(
    body: ResetRequest,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    db: DB,
):
    response.headers["Cache-Control"] = "no-store"
    email_allowed = consume(
        db,
        "reset_email",
        body.email,
        3,
        3600,
        settings.auth_rate_limit_secret,
    )
    origin_allowed = consume(
        db,
        "reset_origin",
        request.client.host if request.client else "unknown",
        10,
        3600,
        settings.auth_rate_limit_secret,
    )
    if not email_allowed or not origin_allowed:
        return GENERIC_RESPONSE

    user = db.scalar(select(User).where(User.email == body.email, User.active.is_(True)))
    if user is None:
        return GENERIC_RESPONSE

    observed_at = now()
    for previous in db.scalars(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.revoked_at.is_(None),
        )
    ):
        previous.revoked_at = observed_at

    raw_token = secrets.token_urlsafe(32)
    reset = PasswordResetToken(
        user_id=user.id,
        token_hash=_digest(raw_token),
        expires_at=observed_at + timedelta(seconds=settings.password_reset_ttl_seconds),
        operation_id=str(uuid4()),
    )
    db.add(reset)
    db.flush()
    background_tasks.add_task(
        _deliver_reset,
        reset.id,
        raw_token,
        user.email,
        user.name,
        reset.operation_id,
    )
    return GENERIC_RESPONSE


@router.post("/validate")
def validate_reset(body: ResetTokenInput, request: Request, db: DB):
    _limit_token_origin(db, request)
    row = _load_token(db, body.token, lock=False)
    user = db.get(User, row.user_id)
    if user is None or not user.active:
        raise _invalid_token()
    return {"status": "valid"}


@router.post("/complete")
def complete_reset(body: ResetComplete, request: Request, db: DB):
    _limit_token_origin(db, request)
    row = _load_token(db, body.token, lock=True)
    user = db.get(User, row.user_id)
    if user is None or not user.active:
        raise _invalid_token()
    try:
        password = validate_new_password(body.password, current_hash=user.password_hash)
    except ValueError as error:
        raise AppError("invalid_password", str(error), 422, fields=["body.password"]) from None

    observed_at = now()
    user.password_hash = hash_password(password)
    row.used_at = observed_at
    for other in db.scalars(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.id != row.id,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.revoked_at.is_(None),
        )
    ):
        other.revoked_at = observed_at
    db.execute(
        update(LoginSession)
        .where(LoginSession.user_id == user.id, LoginSession.revoked.is_(False))
        .values(revoked=True)
    )
    return {"status": "completed"}
