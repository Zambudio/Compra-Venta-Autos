from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.auth.dependencies import AuthContext, require_roles
from app.auth.models import AuthSession
from app.auth.rate_limit import LoginRateLimiter
from app.auth.security import hash_password, hash_token
from app.auth.service import AuthService
from app.core.errors import APIError
from app.users.models import User, UserRole
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.unit
@pytest.mark.asyncio
async def test_auth_service_login_success() -> None:
    db = AsyncMock(spec=AsyncSession)
    password = "a-very-secure-test-password"
    user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash=hash_password(password),
        role=UserRole.OWNER,
        is_active=True,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    db.execute.return_value = mock_result

    service = AuthService(db, session_ttl_seconds=3600)
    auth_session = await service.login("test@example.com", password, "req-123")

    assert auth_session is not None
    assert auth_session.user.email == "test@example.com"
    assert len(auth_session.session_token) >= 32
    assert len(auth_session.csrf_token) >= 32
    assert db.add.call_count >= 2
    assert db.commit.call_count == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_auth_service_login_invalid_password() -> None:
    db = AsyncMock(spec=AsyncSession)
    user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash=hash_password("correct-password"),
        role=UserRole.OWNER,
        is_active=True,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    db.execute.return_value = mock_result

    service = AuthService(db, session_ttl_seconds=3600)
    auth_session = await service.login("test@example.com", "wrong-password", "req-123")

    assert auth_session is None
    assert db.commit.call_count == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_auth_service_login_inactive_user() -> None:
    db = AsyncMock(spec=AsyncSession)
    password = "correct-password"
    user = User(
        id=uuid4(),
        email="inactive@example.com",
        password_hash=hash_password(password),
        role=UserRole.OWNER,
        is_active=False,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    db.execute.return_value = mock_result

    service = AuthService(db, session_ttl_seconds=3600)
    auth_session = await service.login("inactive@example.com", password, "req-123")

    assert auth_session is None
    assert db.commit.call_count == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_auth_service_logout() -> None:
    db = AsyncMock(spec=AsyncSession)
    user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash="fake-hash",
        role=UserRole.OWNER,
        is_active=True,
    )
    session = AuthSession(
        id=uuid4(),
        user_id=user.id,
        token_hash=hash_token("token"),
        csrf_token_hash=hash_token("csrf"),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )

    service = AuthService(db, session_ttl_seconds=3600)
    await service.logout(session, user, "req-456")

    assert session.revoked_at is not None
    assert db.commit.call_count == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rate_limiter_under_and_over_limit() -> None:
    redis = MagicMock()
    redis.eval = AsyncMock(return_value=1)
    limiter = LoginRateLimiter(redis, limit=2, window_seconds=60)

    assert await limiter.check("127.0.0.1", "test@example.com") is True

    redis.eval = AsyncMock(return_value=3)
    assert await limiter.check("127.0.0.1", "test@example.com") is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_roles_allows_matching_role() -> None:
    user = User(
        id=uuid4(),
        email="owner@example.com",
        password_hash="fake",
        role=UserRole.OWNER,
        is_active=True,
    )
    session = AuthSession(
        id=uuid4(),
        user_id=user.id,
        token_hash="hash",
        csrf_token_hash="csrf",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    ctx = AuthContext(user=user, session=session)

    dep = require_roles(UserRole.OWNER, UserRole.ADMIN)
    result = await dep(ctx)
    assert result is ctx


@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_roles_forbids_non_matching_role() -> None:
    user = User(
        id=uuid4(),
        email="viewer@example.com",
        password_hash="fake",
        role=UserRole.VIEWER,
        is_active=True,
    )
    session = AuthSession(
        id=uuid4(),
        user_id=user.id,
        token_hash="hash",
        csrf_token_hash="csrf",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    ctx = AuthContext(user=user, session=session)

    dep = require_roles(UserRole.OWNER)
    with pytest.raises(APIError) as exc:
        await dep(ctx)
    assert exc.value.status_code == 403
