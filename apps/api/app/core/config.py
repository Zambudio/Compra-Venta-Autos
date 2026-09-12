from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import EmailStr, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Environment = Environment.DEVELOPMENT
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"  # noqa: S104 - container bind address
    api_port: int = Field(default=8000, ge=1, le=65535)
    database_url: str
    redis_url: SecretStr
    cors_origins: list[str] = ["http://localhost"]
    allowed_hosts: list[str] = ["localhost", "127.0.0.1"]
    session_cookie_name: str = "motorscope_session"
    csrf_cookie_name: str = "motorscope_csrf"
    session_cookie_secure: bool = True
    session_ttl_seconds: int = Field(default=28_800, ge=900, le=604_800)
    login_rate_limit: int = Field(default=5, ge=1, le=100)
    login_rate_window_seconds: int = Field(default=900, ge=60, le=86_400)
    owner_email: EmailStr | None = None
    owner_password: SecretStr | None = None

    @field_validator("database_url")
    @classmethod
    def require_postgresql(cls, value: str) -> str:
        if not value.startswith("postgresql+psycopg://"):
            raise ValueError("DATABASE_URL must use postgresql+psycopg")
        if "CHANGE_ME" in value:
            raise ValueError("DATABASE_URL still contains a placeholder")
        return value

    @field_validator("redis_url")
    @classmethod
    def require_redis(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value()
        if not raw.startswith(("redis://", "rediss://")):
            raise ValueError("REDIS_URL must use redis or rediss")
        if "CHANGE_ME" in raw:
            raise ValueError("REDIS_URL still contains a placeholder")
        return value

    @field_validator("cors_origins")
    @classmethod
    def reject_wildcard_cors(cls, value: list[str]) -> list[str]:
        if not value or "*" in value:
            raise ValueError("CORS_ORIGINS must be an explicit non-empty allowlist")
        if any(not origin.startswith(("http://", "https://")) for origin in value):
            raise ValueError("CORS origins must be absolute HTTP(S) origins")
        return value

    @field_validator("allowed_hosts")
    @classmethod
    def reject_wildcard_hosts(cls, value: list[str]) -> list[str]:
        if not value or "*" in value:
            raise ValueError("ALLOWED_HOSTS must be an explicit non-empty allowlist")
        return value

    @model_validator(mode="after")
    def enforce_deployed_security(self) -> Settings:
        if self.environment in {Environment.STAGING, Environment.PRODUCTION}:
            if not self.session_cookie_secure:
                raise ValueError("secure session cookies are mandatory outside local/test")
            if any(origin.startswith("http://") for origin in self.cors_origins):
                raise ValueError("deployed CORS origins must use HTTPS")
        return self

    @property
    def redis_dsn(self) -> str:
        return self.redis_url.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    return Settings()
