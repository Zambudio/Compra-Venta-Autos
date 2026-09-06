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
from app.listings.models import VehicleListing
from app.main import create_app
from app.sources.models import SourceSyncRun
from app.users.models import User, UserRole
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

OWNER_PASSWORD = "a secure integration password"
ADMIN_PASSWORD = "another secure integration password"
VIEWER_PASSWORD = "a read only integration password"


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


async def _reset_database(app: FastAPI) -> None:
    async with app.state.database.session_factory() as db:
        await db.execute(delete(SourceSyncRun))
        await db.execute(delete(VehicleListing))
        await db.execute(delete(User))
        db.add_all(
            [
                User(
                    email="owner@example.com",
                    password_hash=hash_password(OWNER_PASSWORD),
                    role=UserRole.OWNER,
                ),
                User(
                    email="admin@example.com",
                    password_hash=hash_password(ADMIN_PASSWORD),
                    role=UserRole.ADMIN,
                ),
                User(
                    email="viewer@example.com",
                    password_hash=hash_password(VIEWER_PASSWORD),
                    role=UserRole.VIEWER,
                ),
            ]
        )
        await db.commit()


@pytest_asyncio.fixture
async def app() -> AsyncIterator[FastAPI]:
    application = create_app(_integration_settings())
    async with application.router.lifespan_context(application):
        await application.state.redis.client.flushdb()
        await _reset_database(application)
        yield application


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as test_client:
        yield test_client


@pytest.fixture
def session_factory(app: FastAPI) -> async_sessionmaker[AsyncSession]:
    factory: async_sessionmaker[AsyncSession] = app.state.database.session_factory
    return factory


async def login(test_client: AsyncClient, email: str, password: str) -> None:
    response = await test_client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text


def csrf_headers(test_client: AsyncClient) -> dict[str, str]:
    return {"X-CSRF-Token": test_client.cookies["motorscope_csrf"]}


@pytest_asyncio.fixture
async def owner_client(client: AsyncClient) -> AsyncClient:
    await login(client, "owner@example.com", OWNER_PASSWORD)
    return client


@pytest_asyncio.fixture
async def viewer_client(client: AsyncClient) -> AsyncClient:
    await login(client, "viewer@example.com", VIEWER_PASSWORD)
    return client
