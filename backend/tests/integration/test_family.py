"""FAMILY-01: isolated family management and owner/member capabilities."""

from datetime import timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.auth import passwords
from app.db.models import Family, FamilyInvite, Membership, User, now
from app.db.unit_of_work import engine, transaction
from app.main import app


def _account(*, family_name="Família Teste", owner_name="Douglas"):
    marker = str(uuid4())
    with Session(engine) as db, db.begin():
        family = Family(name=family_name)
        owner = User(
            email=f"{marker}@test.local",
            name=owner_name,
            password_hash=passwords.hash("testing-password"),
        )
        member = User(
            email=f"member-{marker}@test.local",
            name="Vanessa",
            password_hash=passwords.hash("testing-password"),
        )
        db.add_all([family, owner, member])
        db.flush()
        db.add_all(
            [
                Membership(family_id=family.id, user_id=owner.id, role="owner"),
                Membership(family_id=family.id, user_id=member.id, role="member"),
            ]
        )
        return (
            family.id,
            family.code,
            {"id": owner.id, "email": owner.email, "password_hash": owner.password_hash},
            {"id": member.id, "email": member.email, "password_hash": member.password_hash},
        )


def _client(user):
    client = TestClient(app, client=(str(uuid4()), 123))
    response = client.post(
        "/api/v1/auth/login",
        json={"email": user["email"], "password": "testing-password"},
    )
    assert response.status_code == 200
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    return client


def test_owner_reads_family_members_roles_code_and_capabilities():
    family_id, code, owner, member = _account()
    with _client(owner) as client:
        response = client.get("/api/v1/family")
    assert response.status_code == 200
    assert response.json()["family"] == {
        "id": family_id,
        "name": "Família Teste",
        "code": code,
        "version": 1,
    }
    assert response.json()["members"] == [
        {"id": owner["id"], "name": "Douglas", "role": "owner"},
        {"id": member["id"], "name": "Vanessa", "role": "member"},
    ]
    assert response.json()["capabilities"] == {
        "manage_family": True,
        "manage_invites": True,
    }


def test_member_reads_non_sensitive_data_without_owner_capabilities():
    _, _, _, member = _account()
    with _client(member) as client:
        response = client.get("/api/v1/family")
    assert response.status_code == 200
    assert response.json()["capabilities"] == {
        "manage_family": False,
        "manage_invites": False,
    }
    assert [row["role"] for row in response.json()["members"]] == ["owner", "member"]


def test_family_read_lists_only_pending_invites_without_secrets():
    family_id, _, owner, _ = _account()
    pending_hash = uuid4().hex * 2
    with transaction(family_id) as db:
        pending = FamilyInvite(
            family_id=family_id,
            created_by=owner["id"],
            token_hash=pending_hash,
            expires_at=now() + timedelta(days=7),
        )
        expired = FamilyInvite(
            family_id=family_id,
            created_by=owner["id"],
            token_hash=uuid4().hex * 2,
            expires_at=now() - timedelta(seconds=1),
        )
        db.add_all([pending, expired])
        db.flush()
        pending_id = pending.id
    with _client(owner) as client:
        payload = client.get("/api/v1/family").json()
    assert [invite["id"] for invite in payload["invites"]] == [pending_id]
    assert set(payload["invites"][0]) == {"id", "created_at", "expires_at", "status"}
    assert "token_hash" not in repr(payload)
    assert pending_hash not in repr(payload)


def test_family_read_cannot_select_or_reveal_an_outside_family():
    _, _, owner, _ = _account(family_name="Família A")
    outside_id, outside_code, _, _ = _account(family_name="Família Secreta")
    with _client(owner) as client:
        response = client.get(f"/api/v1/family?family_id={outside_id}")
    assert response.status_code == 200
    assert response.json()["family"]["name"] == "Família A"
    assert response.json()["family"]["id"] != outside_id
    assert response.json()["family"]["code"] != outside_code


def test_family_read_requires_authentication():
    with TestClient(app) as client:
        response = client.get("/api/v1/family")
    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


def test_require_owner_accepts_owner_and_rejects_member():
    from app.api.permissions import require_owner

    family_id, _, owner, member = _account()
    with transaction(family_id) as db:
        assert require_owner(db, family_id, owner["id"]).role == "owner"
        try:
            require_owner(db, family_id, member["id"])
        except Exception as error:
            assert getattr(error, "code", None) == "owner_required"
            assert getattr(error, "status", None) == 403
        else:
            raise AssertionError("member must not receive owner permission")


def test_family_read_does_not_expose_user_email_or_password_hash():
    _, _, owner, _ = _account()
    with _client(owner) as client:
        payload = client.get("/api/v1/family").json()
    assert owner["email"] not in repr(payload)
    assert owner["password_hash"] not in repr(payload)
    assert all(set(member) == {"id", "name", "role"} for member in payload["members"])
