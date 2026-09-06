from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import app.models  # noqa: F401 - verify model registry import
import pytest
from app.auth.cli import create_owner
from app.auth.dependencies import AuthContext, get_db, get_redis, require_auth, require_csrf
from app.auth.models import AuthSession
from app.auth.rate_limit import LoginRateLimiter
from app.auth.service import AuthenticatedSession, AuthService
from app.core.config import Settings
from app.main import create_app
from app.users.models import User, UserRole
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


@pytest.fixture
def mock_user() -> User:
    return User(
        id=uuid4(),
        email="test@example.com",
        password_hash="hash",
        role=UserRole.OWNER,
        is_active=True,
    )


@pytest.fixture
def mock_session(mock_user: User) -> AuthSession:
    return AuthSession(
        id=uuid4(),
        user_id=mock_user.id,
        token_hash="token_hash",
        csrf_token_hash="csrf_hash",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_login_success(mock_user: User, mock_session: AuthSession) -> None:
    app = create_app(make_test_settings())

    async def _dummy_db() -> AsyncIterator[AsyncSession]:
        yield AsyncMock(spec=AsyncSession)

    app.dependency_overrides[get_db] = _dummy_db
    app.dependency_overrides[get_redis] = lambda: AsyncMock(spec=Redis)

    auth_sess = AuthenticatedSession(
        user=mock_user,
        session=mock_session,
        session_token="sess-token-123",
        csrf_token="csrf-token-abc",
    )

    with (
        patch.object(LoginRateLimiter, "check", new_callable=AsyncMock, return_value=True),
        patch.object(AuthService, "login", new_callable=AsyncMock, return_value=auth_sess),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "SuperSecretPassword123!"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "motorscope_session" in response.cookies
    assert "motorscope_csrf" in response.cookies


@pytest.mark.unit
@pytest.mark.asyncio
async def test_login_invalid_credentials() -> None:
    app = create_app(make_test_settings())

    async def _dummy_db() -> AsyncIterator[AsyncSession]:
        yield AsyncMock(spec=AsyncSession)

    app.dependency_overrides[get_db] = _dummy_db
    app.dependency_overrides[get_redis] = lambda: AsyncMock(spec=Redis)

    with (
        patch.object(LoginRateLimiter, "check", new_callable=AsyncMock, return_value=True),
        patch.object(AuthService, "login", new_callable=AsyncMock, return_value=None),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "SuperSecretPassword123!"},
            )

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_login_rate_limited() -> None:
    app = create_app(make_test_settings())

    async def _dummy_db() -> AsyncIterator[AsyncSession]:
        yield AsyncMock(spec=AsyncSession)

    app.dependency_overrides[get_db] = _dummy_db
    app.dependency_overrides[get_redis] = lambda: AsyncMock(spec=Redis)

    with patch.object(LoginRateLimiter, "check", new_callable=AsyncMock, return_value=False):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "SuperSecretPassword123!"},
            )

    assert response.status_code == 429
    assert response.json()["code"] == "login_rate_limited"
    assert "Retry-After" in response.headers


@pytest.mark.unit
@pytest.mark.asyncio
async def test_me_endpoint(mock_user: User, mock_session: AuthSession) -> None:
    app = create_app(make_test_settings())

    ctx = AuthContext(user=mock_user, session=mock_session)
    app.dependency_overrides[require_auth] = lambda: ctx

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == mock_user.email


@pytest.mark.unit
@pytest.mark.asyncio
async def test_logout_endpoint(mock_user: User, mock_session: AuthSession) -> None:
    app = create_app(make_test_settings())

    async def _dummy_db() -> AsyncIterator[AsyncSession]:
        yield AsyncMock(spec=AsyncSession)

    ctx = AuthContext(user=mock_user, session=mock_session)
    app.dependency_overrides[require_csrf] = lambda: ctx
    app.dependency_overrides[get_db] = _dummy_db

    with patch.object(AuthService, "logout", new_callable=AsyncMock, return_value=None):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            response = await client.post("/api/v1/auth/logout")

    assert response.status_code == 200
    assert response.json() == {"success": True}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_readiness_healthy() -> None:
    app = create_app(make_test_settings())
    app.state.database = MagicMock()
    app.state.database.ping = AsyncMock(return_value=True)
    app.state.redis = MagicMock()
    app.state.redis.ping = AsyncMock(return_value=True)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_readiness_unhealthy() -> None:
    app = create_app(make_test_settings())
    app.state.database = MagicMock()
    app.state.database.ping = AsyncMock(side_effect=RuntimeError("db down"))
    app.state.redis = MagicMock()
    app.state.redis.ping = AsyncMock(return_value=True)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json()["code"] == "dependencies_unavailable"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_system_status_endpoint(mock_user: User, mock_session: AuthSession) -> None:
    app = create_app(make_test_settings())
    app.state.database = MagicMock()
    app.state.database.ping = AsyncMock(return_value=True)
    app.state.redis = MagicMock()
    app.state.redis.ping = AsyncMock(return_value=True)

    ctx = AuthContext(user=mock_user, session=mock_session)
    app.dependency_overrides[require_auth] = lambda: ctx

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/api/v1/system/status")

    assert response.status_code == 200
    assert response.json() == {"api": "available", "postgresql": "available", "redis": "ready"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_metrics_endpoint() -> None:
    app = create_app(make_test_settings())

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/api/v1/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cli_create_owner_validations(monkeypatch: pytest.MonkeyPatch) -> None:
    # Missing credentials
    monkeypatch.delenv("OWNER_EMAIL", raising=False)
    monkeypatch.delenv("OWNER_PASSWORD", raising=False)
    assert await create_owner() == 2

    # Placeholder password
    monkeypatch.setenv("OWNER_EMAIL", "owner@example.com")
    monkeypatch.setenv("OWNER_PASSWORD", "CHANGE_ME_NOW_12345")
    assert await create_owner() == 2

    # Password too short
    monkeypatch.setenv("OWNER_PASSWORD", "short")
    assert await create_owner() == 2
