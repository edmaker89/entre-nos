"""AUTH-RESET-01 AC1/2/6/7: generic, hash-only reset delivery."""

import hashlib
import logging
from datetime import timedelta
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db.models import AuthRateLimitWindow, PasswordResetToken, User, now
from app.db.unit_of_work import engine
from app.email.base import EmailDeliveryError, EmailReceipt
from app.main import app
from test_family import _account


GENERIC = {
    "message": "Se existir uma conta para este email, enviaremos as instruções de redefinição."
}


@pytest.fixture(autouse=True)
def isolate_password_reset_state():
    yield
    with Session(engine) as db, db.begin():
        db.execute(delete(PasswordResetToken))
        db.execute(
            delete(AuthRateLimitWindow).where(
                AuthRateLimitWindow.scope.in_(("reset_email", "reset_origin"))
            )
        )


class FakeSender:
    def __init__(self, error=None):
        self.deliveries = []
        self.error = error

    def send(self, message, *, idempotency_key):
        self.deliveries.append((message, idempotency_key))
        if self.error:
            raise self.error
        return EmailReceipt(message_id=f"fake-{len(self.deliveries)}")


def _client(origin=None):
    return TestClient(app, client=(origin or str(uuid4()), 123))


def _request(client, email):
    return client.post("/api/v1/auth/password-reset/request", json={"email": email})


def _token_from(sender):
    url = sender.deliveries[-1][0].text.splitlines()[3]
    return parse_qs(urlparse(url).query)["token"][0]


def test_existing_and_unknown_email_have_identical_public_response(monkeypatch):
    _, _, owner, _ = _account()
    sender = FakeSender()
    monkeypatch.setattr("app.api.password_reset.email_sender", sender)
    with _client() as client:
        existing = _request(client, owner["email"])
        unknown = _request(client, f"unknown-{uuid4()}@test.local")
    assert (existing.status_code, existing.json()) == (202, GENERIC)
    assert (unknown.status_code, unknown.json()) == (202, GENERIC)
    assert len(sender.deliveries) == 1


def test_active_account_gets_https_link_with_fifteen_minute_hash_only_token(monkeypatch):
    _, _, owner, _ = _account(owner_name="Douglas")
    sender = FakeSender()
    monkeypatch.setattr("app.api.password_reset.email_sender", sender)
    monkeypatch.setattr("app.api.password_reset.settings.public_app_url", "https://app.example")
    before = now()
    with _client() as client:
        response = _request(client, owner["email"])
    token = _token_from(sender)
    message, idempotency_key = sender.deliveries[0]
    with Session(engine) as db:
        row = db.scalar(select(PasswordResetToken).where(PasswordResetToken.user_id == owner["id"]))
        assert row.token_hash == hashlib.sha256(token.encode()).hexdigest()
        assert token not in repr(row.__dict__)
        assert before + timedelta(minutes=15) <= row.expires_at <= now() + timedelta(minutes=15)
        assert row.delivery_status == "sent"
        assert row.provider_message_id == "fake-1"
        assert idempotency_key == f"password-reset/{row.id}"
    assert response.json() == GENERIC
    assert message.to == owner["email"]
    assert message.text.splitlines()[3].startswith("https://app.example/reset-password?token=")


def test_unknown_email_creates_no_token_and_sends_nothing(monkeypatch):
    sender = FakeSender()
    monkeypatch.setattr("app.api.password_reset.email_sender", sender)
    with _client() as client:
        response = _request(client, f"missing-{uuid4()}@test.local")
    assert response.status_code == 202
    assert sender.deliveries == []


def test_inactive_account_is_observably_identical_and_not_issued(monkeypatch):
    _, _, owner, _ = _account()
    with Session(engine) as db, db.begin():
        db.get(User, owner["id"]).active = False
    sender = FakeSender()
    monkeypatch.setattr("app.api.password_reset.email_sender", sender)
    with _client() as client:
        response = _request(client, owner["email"])
    assert (response.status_code, response.json(), sender.deliveries) == (202, GENERIC, [])


def test_new_request_revokes_previous_live_token(monkeypatch):
    _, _, owner, _ = _account()
    sender = FakeSender()
    monkeypatch.setattr("app.api.password_reset.email_sender", sender)
    with _client() as client:
        assert _request(client, owner["email"]).status_code == 202
        assert _request(client, owner["email"]).status_code == 202
    with Session(engine) as db:
        rows = db.scalars(
            select(PasswordResetToken)
            .where(PasswordResetToken.user_id == owner["id"])
            .order_by(PasswordResetToken.created_at)
        ).all()
        assert [row.revoked_at is not None for row in rows] == [True, False]
        assert [row.delivery_status for row in rows] == ["sent", "sent"]


def test_fourth_request_for_email_is_limited_without_public_difference(monkeypatch):
    _, _, owner, _ = _account()
    sender = FakeSender()
    monkeypatch.setattr("app.api.password_reset.email_sender", sender)
    with _client() as client:
        responses = [_request(client, owner["email"]) for _ in range(4)]
    assert [(item.status_code, item.json()) for item in responses] == [(202, GENERIC)] * 4
    assert len(sender.deliveries) == 3


def test_eleventh_request_from_origin_is_limited_without_public_difference(monkeypatch):
    accounts = [_account()[2] for _ in range(11)]
    sender = FakeSender()
    monkeypatch.setattr("app.api.password_reset.email_sender", sender)
    with _client(origin=f"origin-{uuid4()}") as client:
        responses = [_request(client, account["email"]) for account in accounts]
    assert [(item.status_code, item.json()) for item in responses] == [(202, GENERIC)] * 11
    assert len(sender.deliveries) == 10


def test_email_lookup_and_limit_are_normalized(monkeypatch):
    _, _, owner, _ = _account()
    sender = FakeSender()
    monkeypatch.setattr("app.api.password_reset.email_sender", sender)
    with _client() as client:
        responses = [
            _request(client, f"  {owner['email'].upper()}  "),
            _request(client, owner["email"]),
            _request(client, owner["email"].upper()),
            _request(client, owner["email"]),
        ]
    assert [(item.status_code, item.json()) for item in responses] == [(202, GENERIC)] * 4
    assert len(sender.deliveries) == 3


def test_provider_failure_is_generic_and_marks_failed_without_secrets(monkeypatch, caplog):
    _, _, owner, _ = _account()
    sender = FakeSender(EmailDeliveryError(status_code=503, retryable=True))
    monkeypatch.setattr("app.api.password_reset.email_sender", sender)
    caplog.set_level(logging.INFO)
    with _client() as client:
        response = _request(client, owner["email"])
    token = _token_from(sender)
    with Session(engine) as db:
        row = db.scalar(select(PasswordResetToken).where(PasswordResetToken.user_id == owner["id"]))
        assert row.delivery_status == "failed"
        assert row.provider_message_id is None
        assert row.operation_id in caplog.text
    assert (response.status_code, response.json()) == (202, GENERIC)
    assert owner["email"] not in caplog.text
    assert token not in caplog.text


def test_provider_timeout_is_generic_and_marks_failed(monkeypatch):
    _, _, owner, _ = _account()
    sender = FakeSender(EmailDeliveryError(status_code=None, retryable=True))
    monkeypatch.setattr("app.api.password_reset.email_sender", sender)
    with _client() as client:
        response = _request(client, owner["email"])
    with Session(engine) as db:
        row = db.scalar(select(PasswordResetToken).where(PasswordResetToken.user_id == owner["id"]))
        assert row.delivery_status == "failed"
    assert (response.status_code, response.json()) == (202, GENERIC)


def test_unexpected_provider_error_never_logs_exception_content(monkeypatch, caplog):
    _, _, owner, _ = _account()
    sender = FakeSender(RuntimeError("provider echoed raw-token-and-email"))
    monkeypatch.setattr("app.api.password_reset.email_sender", sender)
    caplog.set_level(logging.INFO)
    with _client() as client:
        response = _request(client, owner["email"])
    with Session(engine) as db:
        row = db.scalar(select(PasswordResetToken).where(PasswordResetToken.user_id == owner["id"]))
        assert row.delivery_status == "failed"
        assert row.operation_id in caplog.text
    assert (response.status_code, response.json()) == (202, GENERIC)
    assert "raw-token-and-email" not in caplog.text
    assert owner["email"] not in caplog.text


def test_request_is_post_only_and_token_never_appears_in_public_payload(monkeypatch):
    _, _, owner, _ = _account()
    sender = FakeSender()
    monkeypatch.setattr("app.api.password_reset.email_sender", sender)
    with _client() as client:
        get_response = client.get(
            "/api/v1/auth/password-reset/request", params={"email": owner["email"]}
        )
        post_response = _request(client, owner["email"])
    assert get_response.status_code == 405
    assert "token" not in repr(post_response.json()).lower()
    assert owner["email"] not in repr(post_response.json()).lower()


def test_malformed_email_keeps_validation_payload_free_of_submitted_value(monkeypatch):
    sender = FakeSender()
    monkeypatch.setattr("app.api.password_reset.email_sender", sender)
    secret_value = "not-an-address-private-value"
    with _client() as client:
        response = _request(client, secret_value)
    assert response.status_code == 422
    assert secret_value not in repr(response.json())
    assert sender.deliveries == []


def test_success_persists_one_row_per_emission_and_no_raw_secret(monkeypatch):
    _, _, owner, _ = _account()
    sender = FakeSender()
    monkeypatch.setattr("app.api.password_reset.email_sender", sender)
    with _client() as client:
        for _ in range(3):
            assert _request(client, owner["email"]).json() == GENERIC
    tokens = [_token_from_sender.text.split("token=", 1)[1].splitlines()[0] for _token_from_sender, _ in sender.deliveries]
    with Session(engine) as db:
        rows = db.scalars(select(PasswordResetToken).where(PasswordResetToken.user_id == owner["id"])).all()
        assert db.scalar(select(func.count()).select_from(PasswordResetToken).where(PasswordResetToken.user_id == owner["id"])) == 3
        assert all(token not in repr([row.__dict__ for row in rows]) for token in tokens)
