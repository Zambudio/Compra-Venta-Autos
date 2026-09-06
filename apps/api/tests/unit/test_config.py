from typing import Any

import pytest
from app.core.config import Environment, Settings
from pydantic import ValidationError

BASE: dict[str, Any] = {
    "database_url": "postgresql+psycopg://user:password@db:5432/app",
    "redis_url": "redis://:password@redis:6379/0",
    "cors_origins": ["http://localhost"],
    "allowed_hosts": ["localhost"],
    "session_cookie_secure": False,
}


@pytest.mark.unit
def test_development_settings_are_typed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    settings = Settings(_env_file=None, **BASE)
    assert settings.environment is Environment.DEVELOPMENT
    assert settings.session_ttl_seconds == 28_800
    assert settings.redis_dsn.startswith("redis://")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("database_url", "sqlite:///app.db"),
        ("database_url", "postgresql+psycopg://user:CHANGE_ME@db/app"),
        ("redis_url", "http://redis"),
        ("cors_origins", ["*"]),
        ("allowed_hosts", ["*"]),
    ],
)
def test_unsafe_settings_are_rejected(field: str, value: Any) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **(BASE | {field: value}))


@pytest.mark.unit
def test_production_requires_secure_https_configuration() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="production", **BASE)


@pytest.mark.unit
def test_production_accepts_secure_explicit_configuration() -> None:
    settings = Settings(
        _env_file=None,
        **(
            BASE
            | {
                "environment": "production",
                "session_cookie_secure": True,
                "cors_origins": ["https://motorscope.example"],
            }
        ),
    )
    assert settings.environment is Environment.PRODUCTION
