from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.integration.conftest import csrf_headers

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_list_sources_includes_wallapop_and_manual(owner_client: AsyncClient) -> None:
    response = await owner_client.get("/api/v1/sources")

    assert response.status_code == 200
    keys = {item["key"] for item in response.json()}
    # After Phase 10 migration: manual (active), wallapop (active), mock (deactivated but present)
    assert "wallapop" in keys and "manual" in keys
    wallapop = next(item for item in response.json() if item["key"] == "wallapop")
    assert wallapop["is_active"] is True
    assert wallapop["latest_review"] is not None


async def test_source_health(owner_client: AsyncClient) -> None:
    response = await owner_client.get("/api/v1/sources/manual/health")

    assert response.status_code == 200
    assert response.json()["healthy"] is True


async def test_unknown_source_health_is_404(owner_client: AsyncClient) -> None:
    assert (await owner_client.get("/api/v1/sources/mock/health")).status_code == 404


async def test_inactive_source_cannot_sync(owner_client: AsyncClient) -> None:
    """Verify that inactive sources (like wallapop) cannot be synced."""
    response = await owner_client.post(
        "/api/v1/sources/wallapop/sync",
        headers=csrf_headers(owner_client),
        json={"brand": "Seat"},
    )

    # Wallapop is initially inactive (requires API key), so sync should return 409 Conflict
    assert response.status_code == 409
    assert "inactive" in response.json()["detail"].lower()


async def test_sync_requires_csrf(owner_client: AsyncClient) -> None:
    assert (await owner_client.post("/api/v1/sources/manual/sync")).status_code == 403


async def test_viewer_cannot_sync(viewer_client: AsyncClient) -> None:
    response = await viewer_client.post(
        "/api/v1/sources/manual/sync", headers=csrf_headers(viewer_client)
    )
    assert response.status_code == 403
