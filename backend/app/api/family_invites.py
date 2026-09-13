import hashlib
import secrets
from datetime import timedelta
from urllib.parse import quote

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.api.auth import CurrentUser, DB, FamilyID
from app.api.common import operation
from app.api.permissions import require_owner
from app.config import settings
from app.db.models import Audit, FamilyInvite, now
from app.db.unit_of_work import check_version
from app.errors import AppError


router = APIRouter(prefix="/api/v1/family/invites", tags=["family-invites"])


class CreateInvite(BaseModel):
    renew_invite_id: str | None = Field(default=None, max_length=36)


class InviteVersion(BaseModel):
    version: int = Field(ge=1)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@router.post("")
def create_invite(
    body: CreateInvite,
    response: Response,
    request: Request,
    db: DB,
    family_id: FamilyID,
    user: CurrentUser,
):
    require_owner(db, family_id, user.id)
    generated: dict[str, str] = {}

    def apply():
        renewed = None
        if body.renew_invite_id:
            renewed = db.scalar(
                select(FamilyInvite)
                .where(FamilyInvite.id == body.renew_invite_id)
                .with_for_update()
            )
            if renewed is None:
                raise AppError("not_found", "Convite não encontrado.", 404)
            if renewed.used_at is not None or renewed.revoked_at is not None:
                raise AppError("invite_unavailable", "Este convite não está mais disponível.")

        pending = db.scalar(
            select(func.count())
            .select_from(FamilyInvite)
            .where(
                FamilyInvite.family_id == family_id,
                FamilyInvite.used_at.is_(None),
                FamilyInvite.revoked_at.is_(None),
                FamilyInvite.expires_at > now(),
                *(
                    [FamilyInvite.id != body.renew_invite_id]
                    if body.renew_invite_id
                    else []
                ),
            )
        )
        if pending >= 10:
            raise AppError(
                "invite_limit",
                "Há muitos convites pendentes. Revogue um antes de criar outro.",
                429,
            )
        if renewed is not None:
            renewed.revoked_at = now()
            renewed.version += 1

        secret = secrets.token_urlsafe(32)
        invite = FamilyInvite(
            family_id=family_id,
            created_by=user.id,
            token_hash=_hash(secret),
            expires_at=now() + timedelta(seconds=settings.family_invite_ttl_seconds),
        )
        db.add(invite)
        db.flush()
        token = f"{family_id}.{secret}"
        generated["link"] = (
            f"{settings.public_app_url.rstrip('/')}/invite?token={quote(token, safe='')}"
        )
        db.add(
            Audit(
                family_id=family_id,
                actor_id=user.id,
                operation="family.invite.create",
                entity_id=invite.id,
                details={"fields": ["expires_at"]},
            )
        )
        return {"id": invite.id, "expires_at": invite.expires_at.isoformat()}

    result = operation(db, family_id, request, body.model_dump(), apply)
    created_now = "link" in generated
    response.status_code = 201 if created_now else 200
    return {
        **result,
        "link": generated.get("link"),
        "one_time": created_now,
    }


@router.post("/{invite_id}/revoke")
def revoke_invite(
    invite_id: str,
    body: InviteVersion,
    request: Request,
    db: DB,
    family_id: FamilyID,
    user: CurrentUser,
):
    require_owner(db, family_id, user.id)

    def apply():
        invite = db.scalar(
            select(FamilyInvite).where(FamilyInvite.id == invite_id).with_for_update()
        )
        if invite is None:
            raise AppError("not_found", "Convite não encontrado.", 404)
        check_version(invite, body.version)
        if invite.used_at is not None or invite.revoked_at is not None:
            raise AppError("invite_unavailable", "Este convite não está mais disponível.")
        invite.revoked_at = now()
        db.add(
            Audit(
                family_id=family_id,
                actor_id=user.id,
                operation="family.invite.revoke",
                entity_id=invite.id,
                details={"fields": ["revoked_at"]},
            )
        )
        return {"id": invite.id, "status": "revoked", "version": invite.version}

    return operation(db, family_id, request, {"id": invite_id, **body.model_dump()}, apply)
