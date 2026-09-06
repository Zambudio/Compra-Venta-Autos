from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import pytest
from app.auth.dependencies import get_db, get_redis
from app.core.config import Settings
from app.main import create_app
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession


def make_test_settings() -> Settings:
    return Settings(
        _env_file=None,
        environment="test",
        database_url="postgresql+psycopg://user:password@db:5432/test",
        redis_url="redis://:password@redis:6379/0",
        cors_origins=["http://testserver"],
        allowed_hosts=["testserver"],
        session_cookie_secure=False,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_liveness_has_request_id_and_security_headers() -> None:
    app = create_app(make_test_settings())
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/api/v1/health/live", headers={"X-Request-ID": "test-123"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-request-id"] == "test-123"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_invalid_request_id_is_replaced() -> None:
    app = create_app(make_test_settings())
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get(
            "/api/v1/health/live", headers={"X-Request-ID": "invalid id with spaces"}
        )
    assert response.status_code == 200
    assert response.headers["x-request-id"] != "invalid id with spaces"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validation_errors_have_uniform_shape() -> None:
    app = create_app(make_test_settings())

    async def _dummy_db() -> AsyncIterator[AsyncSession]:
        yield AsyncMock(spec=AsyncSession)

    app.dependency_overrides[get_db] = _dummy_db
    app.dependency_overrides[get_redis] = lambda: AsyncMock(spec=Redis)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.post(
            "/api/v1/auth/login", json={"email": "bad", "password": "short"}
        )
    body = response.json()
    assert response.status_code == 422
    assert body["code"] == "validation_error"
    assert body["request_id"] == response.headers["x-request-id"]
    assert "password" not in str(body).lower()
