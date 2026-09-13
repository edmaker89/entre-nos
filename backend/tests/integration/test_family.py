"""FAMILY-01: isolated family management and owner/member capabilities."""

from datetime import timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.auth import passwords
from app.db.models import Audit, Family, FamilyInvite, Membership, User, now
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


def test_owner_renames_family_with_version_idempotency_and_audit():
    family_id, _, owner, _ = _account()
    headers = {"Idempotency-Key": str(uuid4())}
    with _client(owner) as client:
        first = client.patch(
            "/api/v1/family", json={"name": "Casa Silva", "version": 1}, headers=headers
        )
        replay = client.patch(
            "/api/v1/family", json={"name": "Casa Silva", "version": 1}, headers=headers
        )
    assert first.status_code == 200
    assert first.json() == {"id": family_id, "name": "Casa Silva", "version": 2}
    assert replay.json() == first.json()
    with Session(engine) as db:
        audit = db.scalar(
            select(Audit).where(Audit.family_id == family_id, Audit.operation == "family.rename")
        )
        assert audit.actor_id == owner["id"]
        assert audit.details == {"fields": ["name"]}


def test_family_name_must_have_between_one_and_one_hundred_characters():
    _, _, owner, _ = _account()
    with _client(owner) as client:
        blank = client.patch(
            "/api/v1/family",
            json={"name": "   ", "version": 1},
            headers={"Idempotency-Key": str(uuid4())},
        )
        long = client.patch(
            "/api/v1/family",
            json={"name": "x" * 101, "version": 1},
            headers={"Idempotency-Key": str(uuid4())},
        )
    assert blank.status_code == 422
    assert long.status_code == 422


def test_member_cannot_rename_family():
    _, _, _, member = _account()
    with _client(member) as client:
        response = client.patch(
            "/api/v1/family",
            json={"name": "Não pode", "version": 1},
            headers={"Idempotency-Key": str(uuid4())},
        )
    assert response.status_code == 403
    assert response.json()["code"] == "owner_required"


def test_family_rename_rejects_stale_version_without_change():
    family_id, _, owner, _ = _account()
    with _client(owner) as client:
        response = client.patch(
            "/api/v1/family",
            json={"name": "Não aplicar", "version": 9},
            headers={"Idempotency-Key": str(uuid4())},
        )
    assert response.status_code == 409
    assert response.json()["code"] == "version_conflict"
    with Session(engine) as db:
        assert db.get(Family, family_id).name == "Família Teste"


def test_owner_rotates_family_code_and_records_audit():
    family_id, old_code, owner, _ = _account()
    with _client(owner) as client:
        response = client.post(
            "/api/v1/family/code/rotate",
            json={"version": 1},
            headers={"Idempotency-Key": str(uuid4())},
        )
    assert response.status_code == 200
    assert response.json()["code"] != old_code
    assert len(response.json()["code"]) == 10
    assert response.json()["version"] == 2
    with Session(engine) as db:
        audit = db.scalar(
            select(Audit).where(
                Audit.family_id == family_id, Audit.operation == "family.code.rotate"
            )
        )
        assert audit.details == {"fields": ["code"]}


def test_code_rotation_retries_a_collision(monkeypatch):
    _, _, owner, _ = _account()
    _, existing_code, _, _ = _account()
    candidates = iter([existing_code, "ZXCVBNM234"])
    monkeypatch.setattr("app.api.family.family_code", lambda: next(candidates))
    with _client(owner) as client:
        response = client.post(
            "/api/v1/family/code/rotate",
            json={"version": 1},
            headers={"Idempotency-Key": str(uuid4())},
        )
    assert response.status_code == 200
    assert response.json()["code"] == "ZXCVBNM234"


def test_member_cannot_rotate_code_and_owner_cannot_remove_self():
    _, _, owner, member = _account()
    with _client(member) as client:
        denied = client.post(
            "/api/v1/family/code/rotate",
            json={"version": 1},
            headers={"Idempotency-Key": str(uuid4())},
        )
    with _client(owner) as client:
        absent = client.delete(f"/api/v1/family/members/{owner['id']}")
    assert denied.status_code == 403
    assert denied.json()["code"] == "owner_required"
    assert absent.status_code == 404
