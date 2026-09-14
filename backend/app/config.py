from urllib.parse import urlsplit

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", str_strip_whitespace=True)
    database_url: str = "postgresql+psycopg://expense:expense_dev@localhost:55432/expense"
    app_origin: str = "http://localhost:5173"
    secure_cookies: bool = False
    session_absolute_seconds: int = 7 * 86400
    session_idle_seconds: int = 86400
    email_provider: str = "memory"
    resend_api_key: str | None = Field(default=None, repr=False)
    email_from: str = "Entre Nós <noreply@edmaker.dev.br>"
    email_timeout_seconds: float = 5.0
    public_app_url: str = "http://localhost:5173"
    password_reset_ttl_seconds: int = 15 * 60
    family_invite_ttl_seconds: int = 7 * 86400
    auth_rate_limit_secret: str = "local-development-rate-limit-secret"

    @model_validator(mode="after")
    def validate_email_and_public_url(self):
        if self.email_provider not in {"memory", "resend"}:
            raise ValueError("EMAIL_PROVIDER deve ser 'memory' ou 'resend'.")
        if self.email_provider == "resend":
            if not self.resend_api_key:
                raise ValueError("RESEND_API_KEY é obrigatória quando EMAIL_PROVIDER=resend.")
            if not self.email_from:
                raise ValueError("EMAIL_FROM é obrigatório quando EMAIL_PROVIDER=resend.")
        parsed = urlsplit(self.public_app_url)
        if not parsed.scheme or not parsed.hostname:
            raise ValueError("PUBLIC_APP_URL deve ser uma URL absoluta.")
        loopback = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        if not loopback and parsed.scheme != "https":
            raise ValueError("PUBLIC_APP_URL deve usar HTTPS fora do localhost.")
        return self


settings = Settings()
