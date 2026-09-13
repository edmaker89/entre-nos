"""PROFILE-01: authenticated users can read and rename only themselves."""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Audit, User
from app.db.unit_of_work import engine
from test_family import _account, _client


def test_profile_get_returns_own_name_version_and_read_only_login_email():
    _, _, owner, _ = _account()
    with _client(owner) as client:
        response = client.get("/api/v1/profile")
    assert response.status_code == 200
    assert response.json() == {
        "id": owner["id"],
        "name": "Douglas",
        "email": owner["email"],
        "version": 1,
        "email_mutable": False,
    }


def test_profile_patch_updates_me_family_members_and_audit():
    family_id, _, _, member = _account()
    with _client(member) as client:
        changed = client.patch(
            "/api/v1/profile",
            json={"name": "Vanessa Silva", "version": 1},
            headers={"Idempotency-Key": str(uuid4())},
        )
        me = client.get("/api/v1/auth/me")
        family = client.get("/api/v1/family")
    assert changed.status_code == 200
    assert changed.json()["name"] == "Vanessa Silva"
    assert changed.json()["version"] == 2
    assert me.json()["user"]["name"] == "Vanessa Silva"
    assert next(item for item in family.json()["members"] if item["id"] == member["id"])["name"] == "Vanessa Silva"
    with Session(engine) as db:
        audit = db.scalar(select(Audit).where(Audit.family_id == family_id, Audit.operation == "profile.rename"))
        assert audit.actor_id == member["id"]
        assert audit.entity_id == member["id"]
        assert audit.details == {"fields": ["name"]}


def test_profile_name_must_have_between_one_and_one_hundred_characters():
    _, _, owner, _ = _account()
    with _client(owner) as client:
        blank = client.patch(
            "/api/v1/profile",
            json={"name": "  ", "version": 1},
            headers={"Idempotency-Key": str(uuid4())},
        )
        long = client.patch(
            "/api/v1/profile",
            json={"name": "x" * 101, "version": 1},
            headers={"Idempotency-Key": str(uuid4())},
        )
    assert blank.status_code == 422
    assert long.status_code == 422


def test_profile_rejects_email_mutation_and_keeps_login_identity():
    _, _, owner, _ = _account()
    with _client(owner) as client:
        response = client.patch(
            "/api/v1/profile",
            json={"name": "Douglas", "email": "attacker@test.local", "version": 1},
            headers={"Idempotency-Key": str(uuid4())},
        )
    assert response.status_code == 422
    with Session(engine) as db:
        assert db.get(User, owner["id"]).email == owner["email"]


def test_profile_rejects_stale_version_without_changing_name():
    _, _, owner, _ = _account()
    with _client(owner) as client:
        response = client.patch(
            "/api/v1/profile",
            json={"name": "Stale", "version": 8},
            headers={"Idempotency-Key": str(uuid4())},
        )
    assert response.status_code == 409
    assert response.json()["code"] == "version_conflict"
    with Session(engine) as db:
        assert db.get(User, owner["id"]).name == "Douglas"


def test_profile_patch_is_idempotent_and_does_not_duplicate_audit():
    family_id, _, owner, _ = _account()
    headers = {"Idempotency-Key": str(uuid4())}
    with _client(owner) as client:
        first = client.patch("/api/v1/profile", json={"name": "Douglas S.", "version": 1}, headers=headers)
        replay = client.patch("/api/v1/profile", json={"name": "Douglas S.", "version": 1}, headers=headers)
    assert replay.json() == first.json()
    with Session(engine) as db:
        audits = db.scalars(select(Audit).where(Audit.family_id == family_id, Audit.operation == "profile.rename")).all()
        assert len(audits) == 1


def test_profile_has_no_endpoint_for_editing_another_user():
    _, _, owner, member = _account()
    with _client(owner) as client:
        response = client.patch(
            f"/api/v1/profile/{member['id']}",
            json={"name": "Alterado", "version": 1},
            headers={"Idempotency-Key": str(uuid4())},
        )
    assert response.status_code == 404
    with Session(engine) as db:
        assert db.get(User, member["id"]).name == "Vanessa"
