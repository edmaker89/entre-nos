"""AUTH-RESET-01 AC2/AC7: provider-neutral, safe email delivery."""

import json
import logging

import httpx
import pytest

from app.email.base import EmailDeliveryError, EmailMessage
from app.email.memory import MemoryEmailSender
from app.email.resend import ResendEmailSender
from app.email.templates import password_reset_email


def message():
    return EmailMessage(
        to="person@example.com",
        subject="Recupere sua senha",
        text="Use https://app.test/reset?token=secret",
        html='<a href="https://app.test/reset?token=secret">Recuperar</a>',
    )


def sender(handler):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return ResendEmailSender("re_private", "Entre Nós <noreply@example.com>", 2.5, client=client)


def test_memory_sender_records_message_and_idempotency_key():
    delivery = MemoryEmailSender()
    receipt = delivery.send(message(), idempotency_key="password-reset/reset-1")
    assert delivery.deliveries == [(message(), "password-reset/reset-1")]
    assert receipt.message_id == "memory-1"


def test_password_reset_template_escapes_html_and_keeps_text_version():
    rendered = password_reset_email(
        "person@example.com", "<Douglas & Vanessa>", "https://app.test/?token=a&next=b"
    )
    assert rendered.to == "person@example.com"
    assert "&lt;Douglas &amp; Vanessa&gt;" in rendered.html
    assert "token=a&amp;next=b" in rendered.html
    assert "<Douglas & Vanessa>" in rendered.text
    assert "https://app.test/?token=a&next=b" in rendered.text
    assert rendered.subject == "Redefina sua senha — Entre Nós"


def test_resend_success_sends_complete_payload_and_headers():
    observed = {}

    def handler(request):
        observed["authorization"] = request.headers["authorization"]
        observed["idempotency"] = request.headers["idempotency-key"]
        observed["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"id": "email-123"})

    receipt = sender(handler).send(message(), idempotency_key="password-reset/reset-1")
    assert receipt.message_id == "email-123"
    assert observed["authorization"] == "Bearer re_private"
    assert observed["idempotency"] == "password-reset/reset-1"
    assert observed["payload"] == {
        "from": "Entre Nós <noreply@example.com>",
        "to": ["person@example.com"],
        "subject": "Recupere sua senha",
        "text": "Use https://app.test/reset?token=secret",
        "html": '<a href="https://app.test/reset?token=secret">Recuperar</a>',
    }


def test_concurrent_idempotency_conflict_is_retryable():
    delivery = sender(
        lambda _: httpx.Response(409, json={"name": "concurrent_idempotent_requests"})
    )
    with pytest.raises(EmailDeliveryError) as caught:
        delivery.send(message(), idempotency_key="password-reset/reset-1")
    assert caught.value.status_code == 409
    assert caught.value.retryable is True


def test_changed_payload_idempotency_conflict_is_not_retryable():
    delivery = sender(lambda _: httpx.Response(409, json={"name": "invalid_idempotent_request"}))
    with pytest.raises(EmailDeliveryError) as caught:
        delivery.send(message(), idempotency_key="password-reset/reset-1")
    assert caught.value.status_code == 409
    assert caught.value.retryable is False


def test_timeout_is_retryable_without_exposing_secret():
    def timeout(_):
        raise httpx.ReadTimeout("request timed out")

    with pytest.raises(EmailDeliveryError) as caught:
        sender(timeout).send(message(), idempotency_key="password-reset/reset-1")
    assert caught.value.retryable is True
    assert "re_private" not in str(caught.value)
    assert "token=secret" not in str(caught.value)


@pytest.mark.parametrize("status,retryable", [(400, False), (422, False), (500, True), (503, True)])
def test_http_errors_are_classified_without_response_content(status, retryable):
    delivery = sender(lambda _: httpx.Response(status, text="token=secret re_private"))
    with pytest.raises(EmailDeliveryError) as caught:
        delivery.send(message(), idempotency_key="password-reset/reset-1")
    assert caught.value.status_code == status
    assert caught.value.retryable is retryable
    assert "secret" not in str(caught.value)


def test_success_without_provider_id_is_rejected():
    delivery = sender(lambda _: httpx.Response(200, json={}))
    with pytest.raises(EmailDeliveryError) as caught:
        delivery.send(message(), idempotency_key="password-reset/reset-1")
    assert caught.value.status_code == 200
    assert caught.value.retryable is False


def test_delivery_logs_never_contain_api_key_or_message_body(caplog):
    caplog.set_level(logging.INFO)
    delivery = sender(lambda _: httpx.Response(500, text="re_private token=secret"))
    with pytest.raises(EmailDeliveryError):
        delivery.send(message(), idempotency_key="password-reset/reset-1")
    assert "re_private" not in caplog.text
    assert "token=secret" not in caplog.text
