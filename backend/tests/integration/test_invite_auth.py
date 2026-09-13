"""INVITE-01 AC5-7 / D12: POST-only inspection and one-time acceptance."""

from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.auth import passwords
from app.db.models import FamilyInvite, Membership, User
from app.db.unit_of_work import engine, transaction
from app.main import app
from test_family import _account, _client
from test_family_invites import _create


def _token(link):
    return parse_qs(urlparse(link).query)["token"][0]


def _invite(owner):
    with _client(owner) as client:
        return _create(client).json()


def _without_family():
    marker = str(uuid4())
    with Session(engine) as db, db.begin():
        user = User(
            email=f"guest-{marker}@test.local",
            name="Convidado",
            password_hash=passwords.hash("testing-password"),
        )
        db.add(user)
        db.flush()
        return {"id": user.id, "email": user.email}


def test_public_inspection_returns_only_family_name_status_and_expiration():
    _, _, owner, _ = _account(family_name="Casa Silva")
    invite = _invite(owner)
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/invites/inspect", json={"token": _token(invite["link"])})
    assert response.status_code == 200
    assert response.json() == {
        "status": "valid",
        "family_name": "Casa Silva",
        "expires_at": invite["expires_at"],
    }
    assert "token" not in repr(response.json())
    assert "hash" not in repr(response.json())


def test_invite_cannot_be_inspected_with_get_or_without_token():
    with TestClient(app) as client:
        get_response = client.get("/api/v1/auth/invites/inspect?token=secret")
        empty = client.post("/api/v1/auth/invites/inspect", json={"token": ""})
    assert get_response.status_code == 405
    assert empty.status_code == 422


def test_existing_account_without_family_accepts_exact_invited_family():
    family_id, _, owner, _ = _account()
    invite = _invite(owner)
    guest = _without_family()
    with _client(guest) as client:
        response = client.post("/api/v1/auth/invites/accept", json={"token": _token(invite["link"])})
    assert response.status_code == 200
    assert response.json() == {"status": "accepted", "family_id": family_id}
    with Session(engine) as db:
        assert db.get(Membership, (family_id, guest["id"])).role == "member"
        assert db.get(FamilyInvite, invite["id"]).used_by == guest["id"]


def test_account_in_another_family_cannot_accept_invite():
    _, _, owner_a, _ = _account()
    family_b, _, owner_b, _ = _account()
    invite = _invite(owner_a)
    with _client(owner_b) as client:
        response = client.post("/api/v1/auth/invites/accept", json={"token": _token(invite["link"])})
    assert response.status_code == 409
    assert response.json()["code"] == "family_conflict"
    with Session(engine) as db:
        assert db.get(Membership, (family_b, owner_b["id"])).role == "owner"
        assert db.get(FamilyInvite, invite["id"]).used_at is None


def test_account_already_in_same_family_does_not_consume_invite():
    _, _, owner, member = _account()
    invite = _invite(owner)
    with _client(member) as client:
        response = client.post("/api/v1/auth/invites/accept", json={"token": _token(invite["link"])})
    assert response.status_code == 409
    assert response.json()["code"] == "already_member"
    with Session(engine) as db:
        assert db.get(FamilyInvite, invite["id"]).used_at is None


def test_register_creates_account_session_and_membership_only_with_valid_invite():
    family_id, _, owner, _ = _account()
    invite = _invite(owner)
    email = f"new-{uuid4()}@test.local"
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/invites/register",
            json={
                "token": _token(invite["link"]),
                "name": "Nova Pessoa",
                "email": email,
                "password": "  senha Unicode longa 🙂  ",
            },
        )
        me = client.get("/api/v1/auth/me")
    assert response.status_code == 201
    assert response.json()["user"]["name"] == "Nova Pessoa"
    assert response.json()["family_id"] == family_id
    assert "HttpOnly" in response.headers["set-cookie"]
    assert me.status_code == 200
    with Session(engine) as db:
        user = db.scalar(select(User).where(User.email == email))
        assert db.get(Membership, (family_id, user.id)).role == "member"
        assert passwords.verify(user.password_hash, "  senha Unicode longa 🙂  ")


def test_public_registration_is_closed_without_valid_invite():
    with TestClient(app) as client:
        absent = client.post(
            "/api/v1/auth/register",
            json={"name": "X", "email": "x@test.local", "password": "senha bastante longa"},
        )
        invalid = client.post(
            "/api/v1/auth/invites/register",
            json={"token": "not-a-token", "name": "X", "email": "x@test.local", "password": "senha bastante longa"},
        )
    assert absent.status_code == 404
    assert invalid.status_code == 410
    assert invalid.json()["code"] == "invalid_invite"


def test_registration_rejects_existing_email_and_short_password_without_consuming():
    _, _, owner, _ = _account()
    invite = _invite(owner)
    with TestClient(app) as client:
        short = client.post(
            "/api/v1/auth/invites/register",
            json={"token": _token(invite["link"]), "name": "X", "email": "new@test.local", "password": "short"},
        )
        duplicate = client.post(
            "/api/v1/auth/invites/register",
            json={"token": _token(invite["link"]), "name": "X", "email": owner["email"], "password": "senha bastante longa"},
        )
    assert short.status_code == 422
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "email_exists"
    with Session(engine) as db:
        assert db.get(FamilyInvite, invite["id"]).used_at is None


def test_expired_revoked_and_used_invites_are_normalized_as_invalid():
    family_id, _, owner, _ = _account()
    expired = _invite(owner)
    revoked = _invite(owner)
    used = _invite(owner)
    with transaction(family_id) as db:
        from app.db.models import now
        from datetime import timedelta

        db.get(FamilyInvite, expired["id"]).expires_at = now() - timedelta(seconds=1)
        db.get(FamilyInvite, revoked["id"]).revoked_at = now()
        db.get(FamilyInvite, used["id"]).used_at = now()
        db.get(FamilyInvite, used["id"]).used_by = owner["id"]
    with TestClient(app) as client:
        responses = [
            client.post("/api/v1/auth/invites/inspect", json={"token": _token(item["link"])})
            for item in (expired, revoked, used)
        ]
    assert [response.status_code for response in responses] == [410, 410, 410]
    assert [response.json()["code"] for response in responses] == ["invalid_invite"] * 3


def test_token_is_one_time_across_accept_then_inspect_and_register():
    _, _, owner, _ = _account()
    invite = _invite(owner)
    guest = _without_family()
    token = _token(invite["link"])
    with _client(guest) as client:
        assert client.post("/api/v1/auth/invites/accept", json={"token": token}).status_code == 200
    with TestClient(app) as client:
        inspect = client.post("/api/v1/auth/invites/inspect", json={"token": token})
        register = client.post(
            "/api/v1/auth/invites/register",
            json={"token": token, "name": "Outro", "email": f"{uuid4()}@test.local", "password": "senha bastante longa"},
        )
    assert inspect.status_code == 410
    assert register.status_code == 410


def test_two_concurrent_accepts_allow_exactly_one_membership():
    family_id, _, owner, _ = _account()
    invite = _invite(owner)
    guest = _without_family()
    token = _token(invite["link"])

    def accept(_):
        with _client(guest) as client:
            return client.post("/api/v1/auth/invites/accept", json={"token": token}).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(accept, range(2)))
    assert sorted(statuses) == [200, 410]
    with Session(engine) as db:
        count = db.scalar(
            select(func.count()).select_from(Membership).where(
                Membership.family_id == family_id, Membership.user_id == guest["id"]
            )
        )
        assert count == 1


def test_tampered_family_prefix_cannot_cross_family_boundary():
    _, _, owner_a, _ = _account()
    family_b, _, _, _ = _account()
    invite = _invite(owner_a)
    token = _token(invite["link"])
    tampered = family_b + "." + token.split(".", 1)[1]
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/invites/inspect", json={"token": tampered})
    assert response.status_code == 410
    assert response.json()["code"] == "invalid_invite"
