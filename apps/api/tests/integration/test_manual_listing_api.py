from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.integration.conftest import csrf_headers

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_PAYLOAD = {
    "url": "https://example.com/anuncio/xyz",
    "brand": "Seat",
    "model": "Ibiza",
    "year": 2014,
    "mileage_km": 120000,
    "price_amount": "4200",
    "fuel_type": "DIESEL",
    "transmission": "MANUAL",
    "seller_type": "PRIVATE",
    "province": "Murcia",
    "description": "Coche revisado.",
}


async def test_owner_can_register_a_manual_listing(owner_client: AsyncClient) -> None:
    response = await owner_client.post(
        "/api/v1/listings/manual", headers=csrf_headers(owner_client), json=_PAYLOAD
    )

    assert response.status_code == 201
    body = response.json()
    assert body["source_key"] == "manual"
    assert body["brand"] == "SEAT"
    assert body["price_amount"] == "4200.00"

    listed = await owner_client.get("/api/v1/listings?source=manual")
    assert listed.json()["total"] == 1


async def test_duplicate_manual_listing_is_409(owner_client: AsyncClient) -> None:
    headers = csrf_headers(owner_client)
    first = await owner_client.post("/api/v1/listings/manual", headers=headers, json=_PAYLOAD)
    assert first.status_code == 201

    second = await owner_client.post("/api/v1/listings/manual", headers=headers, json=_PAYLOAD)
    assert second.status_code == 409
    assert second.json()["code"] == "listing_already_exists"


async def test_manual_listing_requires_csrf(owner_client: AsyncClient) -> None:
    response = await owner_client.post("/api/v1/listings/manual", json=_PAYLOAD)
    assert response.status_code == 403


async def test_viewer_cannot_register_manual_listing(viewer_client: AsyncClient) -> None:
    response = await viewer_client.post(
        "/api/v1/listings/manual", headers=csrf_headers(viewer_client), json=_PAYLOAD
    )
    assert response.status_code == 403


async def test_invalid_manual_payload_is_422(owner_client: AsyncClient) -> None:
    response = await owner_client.post(
        "/api/v1/listings/manual",
        headers=csrf_headers(owner_client),
        json={**_PAYLOAD, "year": 1700},
    )
    assert response.status_code == 422
