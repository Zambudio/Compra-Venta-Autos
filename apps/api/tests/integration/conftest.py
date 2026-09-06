from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator
from contextlib import suppress

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from app.auth.security import hash_password
from app.core.config import Settings
from app.main import create_app
from app.users.models import User, UserRole
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete


def _integration_settings() -> Settings:
    database_url = os.getenv("TEST_DATABASE_URL")
    redis_url = os.getenv("TEST_REDIS_URL")
    if not database_url or not redis_url:
        pytest.fail("Integration tests require TEST_DATABASE_URL and TEST_REDIS_URL")
    return Settings(
        _env_file=None,
        environment="test",
        database_url=database_url,
        redis_url=redis_url,
        cors_origins=["http://testserver"],
        allowed_hosts=["testserver"],
        session_cookie_secure=False,
        login_rate_limit=2,
        login_rate_window_seconds=60,
    )


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> Iterator[None]:
    settings = _integration_settings()
    os.environ["DATABASE_URL"] = settings.database_url
    os.environ["REDIS_URL"] = settings.redis_dsn
    config = Config("alembic.ini")
    with suppress(Exception):
        command.downgrade(config, "base")
    command.upgrade(config, "head")
    yield
    command.downgrade(config, "base")
    command.upgrade(config, "head")


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    settings = _integration_settings()
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        await app.state.redis.client.flushdb()
        async with app.state.database.session_factory() as db:
            await db.execute(delete(User))
            db.add(
                User(
                    email="owner@example.com",
                    password_hash=hash_password("a secure integration password"),
                    role=UserRole.OWNER,
                )
            )
            await db.commit()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as test_client:
            yield test_client
