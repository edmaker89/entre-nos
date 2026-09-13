import hashlib
import logging
import secrets
from datetime import timedelta
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Request, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.api.auth import DB
from app.config import settings
from app.db.models import PasswordResetToken, User, now
from app.db.unit_of_work import engine
from app.domain.rate_limits import consume
from app.email.base import EmailDeliveryError, EmailSender
from app.email.memory import MemoryEmailSender
from app.email.resend import ResendEmailSender
from app.email.templates import password_reset_email


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
