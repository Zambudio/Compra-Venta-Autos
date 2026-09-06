from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from app.auth.dependencies import AuthContext, get_db, require_auth, require_csrf
from app.auth.models import AuthSession
from app.core.config import Settings
from app.listings.schemas import ListingPage, ListingRead
from app.listings.service import DuplicateManualListingError, ListingNotFoundError, ListingService
from app.listings.vocab import FuelType, ListingStatus, SellerType, Transmission
from app.main import create_app
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


def _client(ctx: AuthContext) -> AsyncClient:
    app = create_app(_settings())
    app.dependency_overrides[require_auth] = lambda: ctx
    app.dependency_overrides[require_csrf] = lambda: ctx
    app.dependency_overrides[get_db] = _dummy_db
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


def _listing() -> ListingRead:
    return ListingRead(
        id=uuid4(),
        source_key="mock",
        external_id="mock-0001",
        url=None,
        brand="SEAT",
        model="Ibiza",
        generation=None,
        trim=None,
        engine_code=None,
        power_kw=66,
        fuel_type=FuelType.DIESEL,
        transmission=Transmission.MANUAL,
        year=2013,
        mileage_km=168000,
        price_amount=Decimal("2800.00"),
        price_currency="EUR",
        location=None,
        province="Murcia",
        seller_type=SellerType.PRIVATE,
        description=None,
        image_urls=[],
        status=ListingStatus.ACTIVE,
        first_seen_at=datetime.now(UTC),
        last_seen_at=datetime.now(UTC),
        published_at=None,
    )


async def test_search_listings_returns_page() -> None:
    page = ListingPage(items=[_listing()], page=1, page_size=20, total=1, has_more=False)
    with patch.object(ListingService, "search", AsyncMock(return_value=page)):
        async with _client(_ctx()) as client:
            response = await client.get("/api/v1/listings?brand=SEAT&page_size=20")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert "payload" not in str(body)
    assert "payload_hash" not in str(body)


async def test_search_rejects_bad_filter() -> None:
    async with _client(_ctx()) as client:
        response = await client.get("/api/v1/listings?year_min=2020&year_max=2010")
    assert response.status_code == 422


async def test_get_listing_not_found_is_404() -> None:
    with patch.object(
        ListingService, "get_detail", AsyncMock(side_effect=ListingNotFoundError(uuid4()))
    ):
        async with _client(_ctx()) as client:
            response = await client.get(f"/api/v1/listings/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["code"] == "listing_not_found"


async def test_create_manual_listing_created() -> None:
    with patch.object(ListingService, "create_manual", AsyncMock(return_value=_listing())):
        async with _client(_ctx()) as client:
            response = await client.post(
                "/api/v1/listings/manual",
                headers={"X-CSRF-Token": "x"},
                json={
                    "brand": "Seat",
                    "model": "Ibiza",
                    "year": 2013,
                    "mileage_km": 168000,
                    "price_amount": "2800",
                    "fuel_type": "DIESEL",
                },
            )
    assert response.status_code == 201
    assert response.json()["brand"] == "SEAT"


async def test_create_manual_duplicate_is_409() -> None:
    with patch.object(
        ListingService,
        "create_manual",
        AsyncMock(side_effect=DuplicateManualListingError(uuid4())),
    ):
        async with _client(_ctx()) as client:
            response = await client.post(
                "/api/v1/listings/manual",
                headers={"X-CSRF-Token": "x"},
                json={
                    "brand": "Seat",
                    "model": "Ibiza",
                    "year": 2013,
                    "mileage_km": 168000,
                    "price_amount": "2800",
                },
            )
    assert response.status_code == 409
    assert response.json()["code"] == "listing_already_exists"


async def test_create_manual_requires_owner_or_admin() -> None:
    async with _client(_ctx(UserRole.VIEWER)) as client:
        response = await client.post(
            "/api/v1/listings/manual",
            headers={"X-CSRF-Token": "x"},
            json={
                "brand": "Seat",
                "model": "Ibiza",
                "year": 2013,
                "mileage_km": 168000,
                "price_amount": "2800",
            },
        )
    assert response.status_code == 403
