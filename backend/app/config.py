from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://expense:expense_dev@localhost:55432/expense"
    app_origin: str = "http://localhost:5173"
    secure_cookies: bool = False
    session_absolute_seconds: int = 7 * 86400
    session_idle_seconds: int = 86400
    email_provider: str = "memory"
    resend_api_key: str | None = None
    email_from: str = "Entre Nós <noreply@edmaker.dev.br>"
    email_timeout_seconds: float = 5.0
    public_app_url: str = "http://localhost:5173"
    family_invite_ttl_seconds: int = 7 * 86400
    auth_rate_limit_secret: str = "local-development-rate-limit-secret"


settings = Settings()
