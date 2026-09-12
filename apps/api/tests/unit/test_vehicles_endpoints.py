from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from app.auth.dependencies import AuthContext, get_db, require_auth, require_csrf
from app.auth.models import AuthSession
from app.core.config import Environment, Settings
from app.listings.vocab import FuelType, Transmission
from app.main import create_app
from app.users.models import User, UserRole
from app.vehicles.errors import (
    MatchCandidateAlreadyDecidedError,
    MatchCandidateNotFoundError,
    VehicleNotFoundError,
)
from app.vehicles.models import MarketEstimate, Vehicle, VehicleMatchCandidate
from app.vehicles.schemas import VehicleHistoryMetrics
from app.vehicles.vocab import MarketEstimateMethod, MatchCandidateStatus
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.unit


def _settings() -> Settings:
    return Settings(
        environment=Environment.TEST,
        database_url="postgresql+psycopg://u:p@db:5432/t",
        redis_url=SecretStr("redis://:p@redis:6379/0"),
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
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    yield mock_session


def _client(ctx: AuthContext) -> AsyncClient:
    app = create_app(_settings())
    app.dependency_overrides[require_auth] = lambda: ctx
    app.dependency_overrides[require_csrf] = lambda: ctx
    app.dependency_overrides[get_db] = _dummy_db
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


def _fake_vehicle(vid: Any = None) -> Vehicle:
    v = Vehicle()
    v.id = vid or uuid4()
    v.brand = "Volkswagen"
    v.model = "Golf"
    v.generation = "VII"
    v.trim = "Advance"
    v.engine_code = "CRBC"
    v.power_kw = 110
    v.fuel_type = FuelType.DIESEL
    v.transmission = Transmission.MANUAL
    v.year = 2017
    v.first_listed_at = datetime(2026, 1, 1, tzinfo=UTC)
    v.listing_count = 1
    v.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    v.updated_at = datetime(2026, 1, 1, tzinfo=UTC)
    v.listings = []
    v.estimates = []
    return v


def _fake_candidate(cid: Any = None, status: MatchCandidateStatus = MatchCandidateStatus.PENDING) -> VehicleMatchCandidate:
    c = VehicleMatchCandidate()
    c.id = cid or uuid4()
    c.listing_a_id = uuid4()
    c.listing_b_id = uuid4()
    c.confidence_score = Decimal("0.850")
    c.match_reasons = {"brand": 1.0, "model": 1.0}
    c.status = status
    c.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    return c


@pytest.mark.asyncio
async def test_list_match_candidates_returns_page() -> None:
    candidate = _fake_candidate()
    client = _client(_ctx())

    with patch(
        "app.vehicles.service.VehicleService.list_match_candidates",
        new=AsyncMock(return_value=([candidate], 1)),
    ):
        async with client as c:
            res = await c.get("/api/v1/match-candidates?status=PENDING&page=1&page_size=20")
            assert res.status_code == 200
            data = res.json()
            assert data["total"] == 1
            assert len(data["items"]) == 1
            assert data["items"][0]["id"] == str(candidate.id)


@pytest.mark.asyncio
async def test_generate_match_candidates_owner_success() -> None:
    client = _client(_ctx(UserRole.OWNER))
    with patch(
        "app.vehicles.service.VehicleService.generate_match_candidates",
        new=AsyncMock(return_value=3),
    ):
        async with client as c:
            res = await c.post("/api/v1/match-candidates/generate")
            assert res.status_code == 200
            assert res.json() == {"created_candidates": 3}


@pytest.mark.asyncio
async def test_generate_match_candidates_viewer_forbidden() -> None:
    client = _client(_ctx(UserRole.VIEWER))
    async with client as c:
        res = await c.post("/api/v1/match-candidates/generate")
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_confirm_match_success() -> None:
    candidate = _fake_candidate()
    vehicle_id = uuid4()
    mock_listing = AsyncMock()
    mock_listing.vehicle_id = vehicle_id
    candidate.listing_a = mock_listing
    candidate.status = MatchCandidateStatus.CONFIRMED

    client = _client(_ctx(UserRole.ADMIN))
    with patch(
        "app.vehicles.service.VehicleService.confirm_match",
        new=AsyncMock(return_value=candidate),
    ):
        async with client as c:
            res = await c.post(f"/api/v1/match-candidates/{candidate.id}/confirm")
            assert res.status_code == 200
            body = res.json()
            assert body["candidate_id"] == str(candidate.id)
            assert body["status"] == "CONFIRMED"
            assert body["vehicle_id"] == str(vehicle_id)


@pytest.mark.asyncio
async def test_confirm_match_not_found() -> None:
    cid = uuid4()
    client = _client(_ctx())
    with patch(
        "app.vehicles.service.VehicleService.confirm_match",
        new=AsyncMock(side_effect=MatchCandidateNotFoundError(cid)),
    ):
        async with client as c:
            res = await c.post(f"/api/v1/match-candidates/{cid}/confirm")
            assert res.status_code == 404
            assert res.json()["code"] == "match_candidate_not_found"


@pytest.mark.asyncio
async def test_confirm_match_already_decided() -> None:
    cid = uuid4()
    client = _client(_ctx())
    with patch(
        "app.vehicles.service.VehicleService.confirm_match",
        new=AsyncMock(side_effect=MatchCandidateAlreadyDecidedError(cid, "REJECTED")),
    ):
        async with client as c:
            res = await c.post(f"/api/v1/match-candidates/{cid}/confirm")
            assert res.status_code == 409
            assert res.json()["code"] == "match_candidate_already_decided"


@pytest.mark.asyncio
async def test_reject_match_success() -> None:
    candidate = _fake_candidate(status=MatchCandidateStatus.REJECTED)
    client = _client(_ctx(UserRole.OWNER))
    with patch(
        "app.vehicles.service.VehicleService.reject_match",
        new=AsyncMock(return_value=candidate),
    ):
        async with client as c:
            res = await c.post(f"/api/v1/match-candidates/{candidate.id}/reject")
            assert res.status_code == 200
            body = res.json()
            assert body["candidate_id"] == str(candidate.id)
            assert body["status"] == "REJECTED"


@pytest.mark.asyncio
async def test_list_vehicles_page() -> None:
    v = _fake_vehicle()
    client = _client(_ctx())
    with patch(
        "app.vehicles.service.VehicleService.list_vehicles",
        new=AsyncMock(return_value=([v], 1)),
    ):
        async with client as c:
            res = await c.get("/api/v1/vehicles?page=1&page_size=20&brand=Volkswagen")
            assert res.status_code == 200
            data = res.json()
            assert data["total"] == 1
            assert data["items"][0]["brand"] == "Volkswagen"


@pytest.mark.asyncio
async def test_get_vehicle_detail_success() -> None:
    v = _fake_vehicle()
    history = VehicleHistoryMetrics(
        lowest_observed_price=Decimal("15000.00"),
        highest_observed_price=Decimal("16500.00"),
        current_min_price=Decimal("15000.00"),
        days_on_market=14,
        total_price_changes=1,
    )
    client = _client(_ctx())
    with (
        patch(
            "app.vehicles.service.VehicleService.get_vehicle_detail",
            new=AsyncMock(return_value=v),
        ),
        patch(
            "app.vehicles.service.VehicleService.get_vehicle_history",
            new=AsyncMock(return_value=history),
        ),
    ):
        async with client as c:
            res = await c.get(f"/api/v1/vehicles/{v.id}")
            assert res.status_code == 200
            data = res.json()
            assert data["id"] == str(v.id)
            assert data["history"]["days_on_market"] == 14


@pytest.mark.asyncio
async def test_get_vehicle_not_found() -> None:
    vid = uuid4()
    client = _client(_ctx())
    with patch(
        "app.vehicles.service.VehicleService.get_vehicle_detail",
        new=AsyncMock(side_effect=VehicleNotFoundError(vid)),
    ):
        async with client as c:
            res = await c.get(f"/api/v1/vehicles/{vid}")
            assert res.status_code == 404
            assert res.json()["code"] == "vehicle_not_found"


@pytest.mark.asyncio
async def test_get_vehicle_history_success() -> None:
    vid = uuid4()
    history = VehicleHistoryMetrics(
        lowest_observed_price=Decimal("10000.00"),
        highest_observed_price=Decimal("12000.00"),
        current_min_price=Decimal("10000.00"),
        days_on_market=30,
        total_price_changes=2,
    )
    client = _client(_ctx())
    with patch(
        "app.vehicles.service.VehicleService.get_vehicle_history",
        new=AsyncMock(return_value=history),
    ):
        async with client as c:
            res = await c.get(f"/api/v1/vehicles/{vid}/history")
            assert res.status_code == 200
            assert res.json()["days_on_market"] == 30


@pytest.mark.asyncio
async def test_compute_vehicle_market_estimate_success() -> None:
    vid = uuid4()
    est = MarketEstimate()
    est.id = uuid4()
    est.vehicle_id = vid
    est.estimated_amount = Decimal("14500.00")
    est.currency = "EUR"
    est.low_amount = Decimal("13800.00")
    est.high_amount = Decimal("15200.00")
    est.number_of_comparables = 10
    est.confidence_score = Decimal("0.850")
    est.method = MarketEstimateMethod.COMPARABLES_MEDIAN_IQR
    est.calculated_at = datetime(2026, 1, 1, tzinfo=UTC)

    client = _client(_ctx(UserRole.OWNER))
    with patch(
        "app.vehicles.service.VehicleService.compute_and_save_market_estimate",
        new=AsyncMock(return_value=est),
    ):
        async with client as c:
            res = await c.post(f"/api/v1/vehicles/{vid}/market-estimate?min_comparables=3")
            assert res.status_code == 200
            body = res.json()
            assert body["estimated_amount"] == "14500.00"
            assert body["number_of_comparables"] == 10
            assert body["method"] == "COMPARABLES_MEDIAN_IQR"
