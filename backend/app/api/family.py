from sqlalchemy import select
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, field_validator

from app.api.auth import CurrentUser, DB, FamilyID
from app.api.common import operation
from app.api.permissions import require_owner
from app.db.models import Audit, Family, FamilyInvite, Membership, User, family_code, now
from app.db.unit_of_work import check_version
from app.errors import AppError


router = APIRouter(prefix="/api/v1/family", tags=["family"])


class FamilyNameUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    version: int = Field(ge=1)

    @field_validator("name")
    @classmethod
    def meaningful_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Informe o nome da família.")
        return value


class VersionInput(BaseModel):
    version: int = Field(ge=1)


@router.get("")
def get_family(db: DB, family_id: FamilyID, user: CurrentUser):
    family = db.get(Family, family_id)
    membership = db.get(Membership, (family_id, user.id))
    members = db.execute(
        select(User.id, User.name, Membership.role)
        .join(Membership, Membership.user_id == User.id)
        .where(Membership.family_id == family_id)
        .order_by(Membership.role.desc(), Membership.created_at, User.id)
    ).all()
    invites = db.scalars(
        select(FamilyInvite)
        .where(
            FamilyInvite.family_id == family_id,
            FamilyInvite.used_at.is_(None),
            FamilyInvite.revoked_at.is_(None),
            FamilyInvite.expires_at > now(),
        )
        .order_by(FamilyInvite.created_at)
    ).all()
    is_owner = membership is not None and membership.role == "owner"
    return {
        "family": {
            "id": family.id,
            "name": family.name,
            "code": family.code,
            "version": family.version,
        },
        "members": [
            {"id": member.id, "name": member.name, "role": member.role}
            for member in members
        ],
        "invites": [
            {
                "id": invite.id,
                "created_at": invite.created_at.isoformat(),
                "expires_at": invite.expires_at.isoformat(),
                "status": "pending",
            }
            for invite in invites
        ],
        "capabilities": {
            "manage_family": is_owner,
            "manage_invites": is_owner,
        },
    }


@router.patch("")
def rename_family(
    body: FamilyNameUpdate,
    request: Request,
    db: DB,
    family_id: FamilyID,
    user: CurrentUser,
):
    require_owner(db, family_id, user.id)

    def apply():
        family = db.get(Family, family_id)
        check_version(family, body.version)
        family.name = body.name
        db.add(
            Audit(
                family_id=family_id,
                actor_id=user.id,
                operation="family.rename",
                entity_id=family_id,
                details={"fields": ["name"]},
            )
        )
        return {"id": family.id, "name": family.name, "version": family.version}

    return operation(db, family_id, request, body.model_dump(), apply)


@router.post("/code/rotate")
def rotate_family_code(
    body: VersionInput,
    request: Request,
    db: DB,
    family_id: FamilyID,
    user: CurrentUser,
):
    require_owner(db, family_id, user.id)

    def apply():
        family = db.get(Family, family_id)
        check_version(family, body.version)
        replacement = None
        for _ in range(10):
            candidate = family_code()
            if db.scalar(select(Family.id).where(Family.code == candidate)) is None:
                replacement = candidate
                break
        if replacement is None:
            raise AppError(
                "family_code_unavailable",
                "Não foi possível gerar um novo código. Tente novamente.",
                503,
            )
        family.code = replacement
        db.add(
            Audit(
                family_id=family_id,
                actor_id=user.id,
                operation="family.code.rotate",
                entity_id=family_id,
                details={"fields": ["code"]},
            )
        )
        return {"id": family.id, "code": family.code, "version": family.version}

    return operation(db, family_id, request, body.model_dump(), apply)


__all__ = ["router", "require_owner"]
