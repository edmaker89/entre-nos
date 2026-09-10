from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://expense:expense_dev@localhost:55432/expense"
    app_origin: str = "http://localhost:5173"
    secure_cookies: bool = False
    session_absolute_seconds: int = 7 * 86400
    session_idle_seconds: int = 86400


settings = Settings()
