from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.integration.conftest import csrf_headers

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_list_sources_includes_mock_and_manual(owner_client: AsyncClient) -> None:
    response = await owner_client.get("/api/v1/sources")

    assert response.status_code == 200
    keys = {item["key"] for item in response.json()}
    assert keys == {"mock", "manual"}
    mock = next(item for item in response.json() if item["key"] == "mock")
    assert mock["latest_review"]["automated_allowed"] is True


async def test_source_health(owner_client: AsyncClient) -> None:
    response = await owner_client.get("/api/v1/sources/mock/health")

    assert response.status_code == 200
    assert response.json()["healthy"] is True


async def test_unknown_source_health_is_404(owner_client: AsyncClient) -> None:
    assert (await owner_client.get("/api/v1/sources/wallapop/health")).status_code == 404


async def test_sync_mock_in_sync_mode_populates_listings(owner_client: AsyncClient) -> None:
    response = await owner_client.post(
        "/api/v1/sources/mock/sync",
        headers=csrf_headers(owner_client),
        json={"brand": "Seat"},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "SUCCESS"
    assert body["listings_created"] >= 1
    assert body["listings_seen"] == body["listings_created"]

    listings = await owner_client.get("/api/v1/listings?brand=Seat")
    assert listings.json()["total"] == body["listings_created"]

    runs = await owner_client.get("/api/v1/sources/mock/sync-runs")
    assert runs.json()[0]["status"] == "SUCCESS"


async def test_sync_requires_csrf(owner_client: AsyncClient) -> None:
    assert (await owner_client.post("/api/v1/sources/mock/sync")).status_code == 403


async def test_viewer_cannot_sync(viewer_client: AsyncClient) -> None:
    response = await viewer_client.post(
        "/api/v1/sources/mock/sync", headers=csrf_headers(viewer_client)
    )
    assert response.status_code == 403
