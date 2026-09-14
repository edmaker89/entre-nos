import pytest
from pydantic import ValidationError

from app.config import Settings


def configured(**changes):
    return Settings(_env_file=None, database_url="postgresql+psycopg://test:test@db/test", **changes)


def test_memory_provider_accepts_http_only_for_loopback_development():
    settings = configured(email_provider="memory", public_app_url="http://127.0.0.1:5173")
    assert settings.public_app_url == "http://127.0.0.1:5173"
    assert settings.email_provider == "memory"


def test_resend_requires_its_api_key():
    with pytest.raises(ValidationError, match="RESEND_API_KEY"):
        configured(email_provider="resend", resend_api_key=None,
                   public_app_url="https://financas.example.com")


def test_resend_requires_a_nonempty_sender():
    with pytest.raises(ValidationError, match="EMAIL_FROM"):
        configured(email_provider="resend", resend_api_key="re_test", email_from="",
                   public_app_url="https://financas.example.com")


def test_public_non_loopback_url_requires_https_for_every_provider():
    with pytest.raises(ValidationError, match="HTTPS"):
        configured(email_provider="memory", public_app_url="http://financas.example.com")


def test_https_deploy_configuration_accepts_resend_without_exposing_the_key():
    settings = configured(email_provider="resend", resend_api_key="re_test",
                          email_from="Entre Nós <noreply@example.com>",
                          public_app_url="https://financas.example.com")
    assert settings.email_provider == "resend"
    assert settings.public_app_url == "https://financas.example.com"
    assert "re_test" not in repr(settings)


def test_unknown_email_provider_is_rejected():
    with pytest.raises(ValidationError, match="EMAIL_PROVIDER"):
        configured(email_provider="smtp", public_app_url="http://localhost:5173")
