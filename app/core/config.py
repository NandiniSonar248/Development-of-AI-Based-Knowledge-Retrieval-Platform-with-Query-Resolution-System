"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the FastAPI application."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI-Powered Intelligent Query Resolution System"
    debug: bool = False

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/AI-QUERY-SYSTEM"
    )

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    access_cookie_name: str = "access_token"
    refresh_cookie_name: str = "refresh_token"

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
