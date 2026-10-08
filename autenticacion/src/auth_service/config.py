"""Application configuration loaded from environment variables / .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AUTH_", env_file=".env", extra="ignore")

    app_name: str = "auth-service"
    host: str = "127.0.0.1"
    port: int = 8000

    database_url: str = "sqlite:///./auth_service.db"

    # NOTE: override AUTH_JWT_SECRET_KEY in production; never ship a hardcoded secret.
    jwt_secret_key: str = "change-this-secret-key-in-production-min-32-bytes"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 60 * 24 * 7


@lru_cache
def get_settings() -> Settings:
    return Settings()
