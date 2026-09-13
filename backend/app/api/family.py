from sqlalchemy import select
from fastapi import APIRouter

from app.api.auth import CurrentUser, DB, FamilyID
from app.api.permissions import require_owner
from app.db.models import Family, FamilyInvite, Membership, User, now


router = APIRouter(prefix="/api/v1/family", tags=["family"])


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


__all__ = ["router", "require_owner"]
