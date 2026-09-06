from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.integration.conftest import csrf_headers

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _seed(owner_client: AsyncClient) -> None:
    response = await owner_client.post(
        "/api/v1/sources/mock/sync", headers=csrf_headers(owner_client)
    )
    assert response.status_code == 202


async def test_search_filters_and_paginates(owner_client: AsyncClient) -> None:
    await _seed(owner_client)

    all_listings = await owner_client.get("/api/v1/listings?page_size=100")
    assert all_listings.status_code == 200
    total = all_listings.json()["total"]
    assert total >= 30

    seat = await owner_client.get("/api/v1/listings?brand=SEAT")
    assert seat.json()["total"] >= 1
    assert all(item["brand"] == "SEAT" for item in seat.json()["items"])

    first_page = await owner_client.get("/api/v1/listings?page=1&page_size=10&sort=price_asc")
    body = first_page.json()
    assert len(body["items"]) == 10
    assert body["has_more"] is True
    prices = [item["price_amount"] for item in body["items"]]
    assert prices == sorted(prices)


async def test_listing_detail_includes_snapshots_and_hides_raw_payload(
    owner_client: AsyncClient,
) -> None:
    await _seed(owner_client)
    listing_id = (await owner_client.get("/api/v1/listings?page_size=1")).json()["items"][0]["id"]

    response = await owner_client.get(f"/api/v1/listings/{listing_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["snapshots"]
    assert "payload" not in body
    assert "payload_hash" not in body


async def test_unknown_listing_is_404(owner_client: AsyncClient) -> None:
    response = await owner_client.get("/api/v1/listings/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["code"] == "listing_not_found"
