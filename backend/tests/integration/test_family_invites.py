"""INVITE-01 AC1/6/8: secure owner-managed invitation lifecycle."""

import hashlib
from datetime import timedelta
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Audit, FamilyInvite, now
from app.db.unit_of_work import engine
from test_family import _account, _client


def _create(client, *, renew_invite_id=None, key=None):
    body = {} if renew_invite_id is None else {"renew_invite_id": renew_invite_id}
    return client.post(
        "/api/v1/family/invites",
        json=body,
        headers={"Idempotency-Key": key or str(uuid4())},
    )


def _secret(link):
    token = parse_qs(urlparse(link).query)["token"][0]
    return token.split(".", 1)[1]


def test_owner_creates_seven_day_invite_and_database_stores_only_hash():
    family_id, _, owner, _ = _account()
    before = now()
    with _client(owner) as client:
        response = _create(client)
    assert response.status_code == 201
    assert response.json()["one_time"] is True
    assert response.json()["link"].startswith("http://localhost:5173/invite?token=")
    secret = _secret(response.json()["link"])
    with Session(engine) as db:
        invite = db.get(FamilyInvite, response.json()["id"])
        assert invite.family_id == family_id
        assert invite.token_hash == hashlib.sha256(secret.encode()).hexdigest()
        assert secret not in repr(invite.__dict__)
        assert before + timedelta(days=7) <= invite.expires_at <= now() + timedelta(days=7)


def test_idempotent_replay_does_not_reveal_token_or_create_another_invite():
    family_id, _, owner, _ = _account()
    key = str(uuid4())
    with _client(owner) as client:
        first = _create(client, key=key)
        replay = _create(client, key=key)
    assert first.json()["link"]
    assert replay.status_code == 200
    assert replay.json()["id"] == first.json()["id"]
    assert replay.json()["link"] is None
    assert replay.json()["one_time"] is False
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(FamilyInvite).where(FamilyInvite.family_id == family_id)) == 1


def test_family_listing_never_returns_invite_hash_or_link():
    _, _, owner, _ = _account()
    with _client(owner) as client:
        created = _create(client).json()
        payload = client.get("/api/v1/family").json()
    assert payload["invites"][0]["id"] == created["id"]
    assert "link" not in repr(payload)
    assert "token" not in repr(payload)
    assert _secret(created["link"]) not in repr(payload)


def test_member_cannot_create_invite():
    _, _, _, member = _account()
    with _client(member) as client:
        response = _create(client)
    assert response.status_code == 403
    assert response.json()["code"] == "owner_required"


def test_family_is_limited_to_ten_pending_invites():
    _, _, owner, _ = _account()
    with _client(owner) as client:
        for _ in range(10):
            assert _create(client).status_code == 201
        limited = _create(client)
    assert limited.status_code == 429
    assert limited.json()["code"] == "invite_limit"


def test_owner_revokes_pending_invite_with_version_and_audit():
    family_id, _, owner, _ = _account()
    with _client(owner) as client:
        invite = _create(client).json()
        response = client.post(
            f"/api/v1/family/invites/{invite['id']}/revoke",
            json={"version": 1},
            headers={"Idempotency-Key": str(uuid4())},
        )
    assert response.status_code == 200
    assert response.json() == {"id": invite["id"], "status": "revoked", "version": 2}
    with Session(engine) as db:
        row = db.get(FamilyInvite, invite["id"])
        assert row.revoked_at is not None
        audit = db.scalar(select(Audit).where(Audit.family_id == family_id, Audit.operation == "family.invite.revoke"))
        assert audit.details == {"fields": ["revoked_at"]}


def test_member_cannot_revoke_invite():
    _, _, owner, member = _account()
    with _client(owner) as client:
        invite = _create(client).json()
    with _client(member) as client:
        response = client.post(
            f"/api/v1/family/invites/{invite['id']}/revoke",
            json={"version": 1},
            headers={"Idempotency-Key": str(uuid4())},
        )
    assert response.status_code == 403
    assert response.json()["code"] == "owner_required"


def test_renewing_invite_revokes_previous_and_returns_new_one_time_link():
    _, _, owner, _ = _account()
    with _client(owner) as client:
        old = _create(client).json()
        renewed = _create(client, renew_invite_id=old["id"])
    assert renewed.status_code == 201
    assert renewed.json()["id"] != old["id"]
    assert renewed.json()["link"] != old["link"]
    with Session(engine) as db:
        assert db.get(FamilyInvite, old["id"]).revoked_at is not None


def test_revoked_invite_is_not_listed_and_revoke_rejects_stale_version():
    _, _, owner, _ = _account()
    with _client(owner) as client:
        invite = _create(client).json()
        first = client.post(
            f"/api/v1/family/invites/{invite['id']}/revoke",
            json={"version": 1},
            headers={"Idempotency-Key": str(uuid4())},
        )
        stale = client.post(
            f"/api/v1/family/invites/{invite['id']}/revoke",
            json={"version": 1},
            headers={"Idempotency-Key": str(uuid4())},
        )
        listed = client.get("/api/v1/family").json()["invites"]
    assert first.status_code == 200
    assert stale.status_code == 409
    assert stale.json()["code"] in {"version_conflict", "invite_unavailable"}
    assert invite["id"] not in [item["id"] for item in listed]


def test_owner_cannot_revoke_invite_from_another_family():
    _, _, owner_a, _ = _account()
    _, _, owner_b, _ = _account()
    with _client(owner_b) as client:
        foreign = _create(client).json()
    with _client(owner_a) as client:
        response = client.post(
            f"/api/v1/family/invites/{foreign['id']}/revoke",
            json={"version": 1},
            headers={"Idempotency-Key": str(uuid4())},
        )
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"
