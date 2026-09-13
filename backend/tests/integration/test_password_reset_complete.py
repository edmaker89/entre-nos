"""AUTH-RESET-01 AC3-5/8: one-time, atomic password reset completion."""

import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.auth import passwords
from app.db.models import AuthRateLimitWindow, PasswordResetToken, Session as LoginSession, User, now
from app.db.unit_of_work import engine
from app.domain.passwords import verify_password
from app.email.base import EmailReceipt
from app.main import app
from test_family import _account


INVALID = {
    "code": "invalid_or_expired_token",
    "message": "Este link expirou ou não está mais disponível. Solicite uma nova redefinição.",
}


class FakeSender:
    def __init__(self):
        self.deliveries = []

    def send(self, message, *, idempotency_key):
        self.deliveries.append((message, idempotency_key))
        return EmailReceipt(message_id=f"fake-{len(self.deliveries)}")


@pytest.fixture(autouse=True)
def isolate_password_reset_state():
    yield
    with Session(engine) as db, db.begin():
        db.execute(delete(PasswordResetToken))
        db.execute(
            delete(AuthRateLimitWindow).where(
                AuthRateLimitWindow.scope.in_(
                    ("reset_email", "reset_origin", "reset_token_origin")
                )
            )
        )


def _client():
    return TestClient(app, client=(str(uuid4()), 123))


def _issue(monkeypatch, account):
    sender = FakeSender()
    monkeypatch.setattr("app.api.password_reset.email_sender", sender)
    with _client() as client:
        response = client.post(
            "/api/v1/auth/password-reset/request", json={"email": account["email"]}
        )
    assert response.status_code == 202
    url = sender.deliveries[0][0].text.splitlines()[3]
    return parse_qs(urlparse(url).query)["token"][0]


def _validate(token):
    with _client() as client:
        return client.post("/api/v1/auth/password-reset/validate", json={"token": token})


def _complete(token, password):
    with _client() as client:
        return client.post(
            "/api/v1/auth/password-reset/complete",
            json={"token": token, "password": password},
        )


def _row(account):
    with Session(engine) as db:
        return db.scalar(
            select(PasswordResetToken).where(PasswordResetToken.user_id == account["id"])
        )


def test_validate_accepts_sent_live_token_without_consuming_it(monkeypatch):
    _, _, owner, _ = _account()
    token = _issue(monkeypatch, owner)
    first = _validate(token)
    second = _validate(token)
    row = _row(owner)
    assert (first.status_code, first.json()) == (200, {"status": "valid"})
    assert (second.status_code, second.json()) == (200, {"status": "valid"})
    assert row.used_at is None
    assert row.revoked_at is None


@pytest.mark.parametrize("state", ["expired", "used", "revoked", "failed"])
def test_invalid_token_states_are_normalized(monkeypatch, state):
    _, _, owner, _ = _account()
    token = _issue(monkeypatch, owner)
    with Session(engine) as db, db.begin():
        row = db.scalar(
            select(PasswordResetToken).where(PasswordResetToken.user_id == owner["id"])
        )
        if state == "expired":
            row.expires_at = now() - timedelta(seconds=1)
        elif state == "used":
            row.used_at = now()
        elif state == "revoked":
            row.revoked_at = now()
        else:
            row.delivery_status = "failed"
    response = _validate(token)
    assert response.status_code == 410
    assert {key: response.json()[key] for key in ("code", "message")} == INVALID
    assert token not in repr(response.json())


def test_unknown_and_malformed_tokens_have_same_normalized_response():
    unknown = _validate("a" * 43)
    malformed = _validate("not-a-token")
    assert unknown.status_code == malformed.status_code == 410
    assert {key: unknown.json()[key] for key in ("code", "message")} == INVALID
    assert {key: malformed.json()[key] for key in ("code", "message")} == INVALID


def test_complete_accepts_unicode_spaces_and_revokes_sessions_and_tokens(monkeypatch):
    _, _, owner, _ = _account()
    first_token = _issue(monkeypatch, owner)
    second_token = _issue(monkeypatch, owner)
    with Session(engine) as db, db.begin():
        first_row = db.scalar(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == hashlib.sha256(first_token.encode()).hexdigest()
            )
        )
        first_row.revoked_at = None
    session_ids = []
    for _ in range(2):
        with _client() as client:
            login = client.post(
                "/api/v1/auth/login",
                json={"email": owner["email"], "password": "testing-password"},
            )
            assert login.status_code == 200
        with Session(engine) as db:
            session_ids.append(
                db.scalars(
                    select(LoginSession.id)
                    .where(LoginSession.user_id == owner["id"])
                    .order_by(LoginSession.created_at.desc())
                ).first()
            )
    new_password = "  uma senha Unicode longa 🙂  "
    response = _complete(second_token, new_password)
    assert (response.status_code, response.json()) == (200, {"status": "completed"})
    with Session(engine) as db:
        user = db.get(User, owner["id"])
        rows = db.scalars(
            select(PasswordResetToken).where(PasswordResetToken.user_id == owner["id"])
        ).all()
        sessions = db.scalars(
            select(LoginSession).where(LoginSession.id.in_(session_ids))
        ).all()
        assert passwords.verify(user.password_hash, new_password)
        assert sorted((row.used_at is not None, row.revoked_at is not None) for row in rows) == [
            (False, True),
            (True, False),
        ]
        assert all(session.revoked is True for session in sessions)
    assert _validate(second_token).status_code == 410
    assert _validate(first_token).status_code == 410


def test_complete_rejects_current_password_without_changing_state(monkeypatch):
    _, _, owner, _ = _account()
    token = _issue(monkeypatch, owner)
    before_hash = owner["password_hash"]
    response = _complete(token, "testing-password")
    assert response.status_code == 422
    assert response.json()["code"] == "invalid_password"
    assert response.json()["fields"] == ["body.password"]
    with Session(engine) as db:
        assert db.get(User, owner["id"]).password_hash == before_hash
        assert db.scalar(select(PasswordResetToken).where(PasswordResetToken.user_id == owner["id"])).used_at is None


@pytest.mark.parametrize("password", ["curta", "x" * 201])
def test_complete_rejects_password_outside_fifteen_to_two_hundred(monkeypatch, password):
    _, _, owner, _ = _account()
    token = _issue(monkeypatch, owner)
    response = _complete(token, password)
    assert response.status_code == 422
    assert response.json()["code"] == "invalid_password"
    assert _row(owner).used_at is None


def test_used_token_cannot_change_password_again(monkeypatch):
    _, _, owner, _ = _account()
    token = _issue(monkeypatch, owner)
    accepted = _complete(token, "primeira senha nova válida")
    rejected = _complete(token, "segunda senha nova válida")
    assert accepted.status_code == 200
    assert rejected.status_code == 410
    assert {key: rejected.json()[key] for key in ("code", "message")} == INVALID
    with Session(engine) as db:
        assert passwords.verify(db.get(User, owner["id"]).password_hash, "primeira senha nova válida")


def test_completion_with_unknown_token_does_not_change_any_password():
    _, _, owner, _ = _account()
    response = _complete("z" * 43, "uma nova senha bastante longa")
    assert response.status_code == 410
    assert {key: response.json()[key] for key in ("code", "message")} == INVALID
    with Session(engine) as db:
        assert db.get(User, owner["id"]).password_hash == owner["password_hash"]


def test_two_concurrent_completions_allow_exactly_one_winner(monkeypatch):
    _, _, owner, _ = _account()
    token = _issue(monkeypatch, owner)
    barrier = Barrier(2)

    def complete(index):
        barrier.wait()
        return _complete(token, f"senha concorrente válida {index}")

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(complete, (1, 2)))
    assert sorted(response.status_code for response in responses) == [200, 410]
    with Session(engine) as db:
        user = db.get(User, owner["id"])
        assert sum(
            verify_password(user.password_hash, candidate)
            for candidate in ("senha concorrente válida 1", "senha concorrente válida 2")
        ) == 1
        row = db.scalar(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == hashlib.sha256(token.encode()).hexdigest()
            )
        )
        assert row.used_at is not None


def test_inactive_user_token_is_normalized_and_cannot_reset(monkeypatch):
    _, _, owner, _ = _account()
    token = _issue(monkeypatch, owner)
    with Session(engine) as db, db.begin():
        db.get(User, owner["id"]).active = False
    response = _complete(token, "uma nova senha bastante longa")
    assert response.status_code == 410
    assert {key: response.json()[key] for key in ("code", "message")} == INVALID
    assert _row(owner).used_at is None
