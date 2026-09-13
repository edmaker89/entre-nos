from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.auth import CurrentUser, DB, FamilyID
from app.api.common import operation
from app.db.models import Audit, User
from app.db.unit_of_work import check_version


router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    version: int = Field(ge=1)

    @field_validator("name")
    @classmethod
    def meaningful_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Informe seu nome.")
        return value


def _serialize(user: User):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "version": user.version,
        "email_mutable": False,
    }


@router.get("")
def get_profile(user: CurrentUser, family_id: FamilyID):
    return _serialize(user)


@router.patch("")
def update_profile(
    body: ProfileUpdate,
    request: Request,
    db: DB,
    family_id: FamilyID,
    user: CurrentUser,
):
    def apply():
        current = db.get(User, user.id)
        check_version(current, body.version)
        current.name = body.name
        db.add(
            Audit(
                family_id=family_id,
                actor_id=user.id,
                operation="profile.rename",
                entity_id=user.id,
                details={"fields": ["name"]},
            )
        )
        return _serialize(current)

    return operation(db, family_id, request, body.model_dump(), apply)
