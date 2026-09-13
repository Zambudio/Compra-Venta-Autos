from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from unittest.mock import ANY, AsyncMock, patch
from uuid import uuid4

import pytest
from app.auth.dependencies import AuthContext, get_db, get_redis, require_auth, require_csrf
from app.auth.models import AuthSession
from app.connectors.errors import UnknownConnectorError
from app.core.config import Settings
from app.listings.vocab import ProviderKind, SyncRunStatus
from app.main import create_app
from app.sources.schemas import SourceConfigRead, SourceHealthRead, SourceRead, SyncRunRead
from app.sources.service import LastActiveSourceError, SourceNotFoundError, SourceService
from app.users.models import User, UserRole
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.unit


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        environment="test",
        database_url="postgresql+psycopg://u:p@db:5432/t",
        redis_url="redis://:p@redis:6379/0",
        cors_origins=["http://testserver"],
        allowed_hosts=["testserver"],
        session_cookie_secure=False,
    )


def _ctx(role: UserRole = UserRole.OWNER) -> AuthContext:
    user = User(id=uuid4(), email="u@example.com", password_hash="h", role=role, is_active=True)
    session = AuthSession(
        id=uuid4(),
        user_id=user.id,
        token_hash="t",
        csrf_token_hash="c",
        expires_at=datetime(2999, 1, 1, tzinfo=UTC),
    )
    return AuthContext(user=user, session=session)


async def _dummy_db() -> AsyncIterator[AsyncSession]:
    yield AsyncMock(spec=AsyncSession)


def _client(app_ctx: AuthContext) -> AsyncClient:
    app = create_app(_settings())
    app.dependency_overrides[require_auth] = lambda: app_ctx
    app.dependency_overrides[require_csrf] = lambda: app_ctx
    app.dependency_overrides[get_db] = _dummy_db
    app.dependency_overrides[get_redis] = lambda: AsyncMock()
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


async def test_list_sources_returns_catalog() -> None:
    sources = [
        SourceRead(
            key="wallapop",
            name="Wallapop",
            provider_kind=ProviderKind.CONNECTOR,
            is_active=False,
            is_automatable=False,
            latest_review=None,
        )
    ]
    with patch.object(SourceService, "list_sources", AsyncMock(return_value=sources)):
        async with _client(_ctx()) as client:
            response = await client.get("/api/v1/sources")
    assert response.status_code == 200
    assert response.json()[0]["key"] == "wallapop"


async def test_owner_can_deactivate_a_source() -> None:
    updated = SourceRead(
        key="manual",
        name="Entrada manual",
        provider_kind=ProviderKind.MANUAL,
        is_active=False,
        is_automatable=True,
        latest_review=None,
    )
    update = AsyncMock(return_value=updated)
    with patch.object(SourceService, "update_source", update):
        async with _client(_ctx()) as client:
            response = await client.patch(
                "/api/v1/sources/manual",
                json={"is_active": False},
                headers={"X-CSRF-Token": "x"},
            )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    update.assert_awaited_once_with("manual", is_active=False, changed_by=ANY)


async def test_viewer_cannot_change_a_source() -> None:
    async with _client(_ctx(UserRole.VIEWER)) as client:
        response = await client.patch(
            "/api/v1/sources/manual",
            json={"is_active": False},
            headers={"X-CSRF-Token": "x"},
        )

    assert response.status_code == 403


async def test_owner_can_update_source_configuration() -> None:
    now = datetime.now(UTC)
    updated = SourceConfigRead(
        key="wallapop",
        enabled=False,
        config={"timeout": 15},
        last_sync=None,
        sync_error=None,
        updated_at=now,
    )
    update = AsyncMock(return_value=updated)
    with patch.object(SourceService, "update_source_config", update):
        async with _client(_ctx()) as client:
            response = await client.patch(
                "/api/v1/sources/wallapop/config",
                json={"enabled": False, "config": {"timeout": 15}},
                headers={"X-CSRF-Token": "x"},
            )

    assert response.status_code == 200
    assert response.json()["enabled"] is False
    update.assert_awaited_once_with(
        "wallapop", enabled=False, config={"timeout": 15}, changed_by=ANY
    )


async def test_source_configuration_maps_last_active_error_to_400() -> None:
    with patch.object(
        SourceService,
        "update_source_config",
        AsyncMock(side_effect=LastActiveSourceError("manual")),
    ):
        async with _client(_ctx()) as client:
            response = await client.patch(
                "/api/v1/sources/manual/config",
                json={"enabled": False},
                headers={"X-CSRF-Token": "x"},
            )

    assert response.status_code == 400
    assert response.json()["code"] == "active_source_required"


async def test_viewer_cannot_update_source_configuration() -> None:
    async with _client(_ctx(UserRole.VIEWER)) as client:
        response = await client.patch(
            "/api/v1/sources/wallapop/config",
            json={"enabled": False},
            headers={"X-CSRF-Token": "x"},
        )

    assert response.status_code == 403


async def test_source_health_maps_unknown_to_404() -> None:
    with patch.object(
        SourceService, "health", AsyncMock(side_effect=UnknownConnectorError("nope"))
    ):
        async with _client(_ctx()) as client:
            response = await client.get("/api/v1/sources/nope/health")
    assert response.status_code == 404
    assert response.json()["code"] == "source_not_found"


async def test_source_health_ok() -> None:
    health = SourceHealthRead(
        source_key="manual", healthy=True, detail="ok", checked_at=datetime.now(UTC)
    )
    with patch.object(SourceService, "health", AsyncMock(return_value=health)):
        async with _client(_ctx()) as client:
            response = await client.get("/api/v1/sources/manual/health")
    assert response.status_code == 200
    assert response.json()["healthy"] is True


async def test_sync_sync_mode_runs_and_returns_result() -> None:
    run_id = uuid4()
    created = AsyncMock()
    created.id = run_id
    executed = SyncRunRead(
        id=run_id,
        source_key="wallapop",
        status=SyncRunStatus.SUCCESS,
        mode="sync",
        listings_seen=36,
        listings_created=36,
        listings_updated=0,
        snapshots_created=36,
        error_summary=None,
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    with (
        patch.object(SourceService, "create_run", AsyncMock(return_value=created)),
        patch.object(SourceService, "execute_run", AsyncMock(return_value=created)),
        patch("app.sources.router.run_read", return_value=executed),
    ):
        async with _client(_ctx()) as client:
            response = await client.post(
                "/api/v1/sources/wallapop/sync", headers={"X-CSRF-Token": "x"}
            )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "SUCCESS"
    assert body["listings_created"] == 36


async def test_sync_requires_owner_or_admin_role() -> None:
    async with _client(_ctx(UserRole.VIEWER)) as client:
        response = await client.post("/api/v1/sources/wallapop/sync", headers={"X-CSRF-Token": "x"})
    assert response.status_code == 403


async def test_sync_runs_unknown_source_is_404() -> None:
    with patch.object(
        SourceService, "list_sync_runs", AsyncMock(side_effect=SourceNotFoundError("nope"))
    ):
        async with _client(_ctx()) as client:
            response = await client.get("/api/v1/sources/nope/sync-runs")
    assert response.status_code == 404
