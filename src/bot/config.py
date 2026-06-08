from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Telegram
    bot_token: str
    # Public HTTPS base. If empty, derived from Railway's RAILWAY_PUBLIC_DOMAIN,
    # else falls back to localhost (fine for polling / local dev).
    public_base_url: str = ""
    telegram_webhook_secret: str = "change-me"

    # Linear OAuth (actor=app)
    linear_client_id: str = ""
    linear_client_secret: str = ""
    # If empty, derived as {base_url}/linear/oauth/callback.
    linear_redirect_uri: str = ""
    linear_webhook_secret: str = ""

    # Storage
    database_url: str = "postgresql+asyncpg://lineartg:lineartg@localhost:5432/lineartg"
    redis_url: str = "redis://localhost:6379/0"

    # AI assistant (optional). Empty ai_provider disables the assistant.
    ai_provider: str = ""  # "anthropic" | "openai" | "" (off)
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    ai_model: str = ""  # optional override; sensible default per provider

    # App
    bootstrap_admin_ids: str = ""
    default_lang: str = "ru"
    log_level: str = "INFO"
    web_host: str = "0.0.0.0"
    web_port: int = 8080

    # Platform-injected (Railway/Render set PORT; Railway sets the public domain).
    port: int | None = Field(default=None, validation_alias="PORT")
    railway_public_domain: str | None = Field(
        default=None, validation_alias="RAILWAY_PUBLIC_DOMAIN"
    )

    @field_validator("database_url")
    @classmethod
    def _normalize_db_url(cls, v: str) -> str:
        """Railway/Heroku hand out postgres:// URLs; SQLAlchemy async needs the
        asyncpg driver explicitly."""
        if v.startswith("postgresql+asyncpg://"):
            return v
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def base_url(self) -> str:
        if self.public_base_url:
            return self.public_base_url.rstrip("/")
        if self.railway_public_domain:
            return f"https://{self.railway_public_domain}".rstrip("/")
        return "http://localhost:8080"

    @property
    def redirect_uri(self) -> str:
        return self.linear_redirect_uri or f"{self.base_url}/linear/oauth/callback"

    @property
    def bind_port(self) -> int:
        return self.port or self.web_port

    @property
    def admin_ids(self) -> set[int]:
        return {
            int(x) for x in self.bootstrap_admin_ids.replace(" ", "").split(",") if x
        }

    @property
    def ai_enabled(self) -> bool:
        if self.ai_provider == "anthropic":
            return bool(self.anthropic_api_key)
        if self.ai_provider == "openai":
            return bool(self.openai_api_key)
        return False

    @property
    def ai_model_name(self) -> str:
        if self.ai_model:
            return self.ai_model
        return "claude-sonnet-4-20250514" if self.ai_provider == "anthropic" else "gpt-4o-mini"

    @property
    def telegram_webhook_path(self) -> str:
        return f"/tg/webhook/{self.telegram_webhook_secret}"

    @property
    def telegram_webhook_url(self) -> str:
        return f"{self.base_url}{self.telegram_webhook_path}"


settings = Settings()  # type: ignore[call-arg]
