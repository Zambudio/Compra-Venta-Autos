"""Tests unitarios para los endpoints de la API de scoring y oportunidades."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal
import typing
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from app.auth.dependencies import AuthContext, get_db, require_auth, require_csrf
from app.auth.models import AuthSession
from app.core.config import Environment, Settings
from app.main import create_app
from app.scoring.models import Opportunity, ScoringProfile, ScoringProfileVersion
from app.scoring.vocab import (
    DEFAULT_SCORING_WEIGHTS,
    ConfidenceLevel,
    OpportunityStatus,
    SellerPressureLevel,
)
from app.users.models import User, UserRole
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


def _fake_opportunity(op_id: typing.Any = None) -> Opportunity:
    now = datetime.now(UTC)
    op = Opportunity(
        id=op_id or uuid4(),
        status=OpportunityStatus.IDENTIFIED,
        currency="EUR",
        asking_price=Decimal("1750.00"),
        estimated_market_price=Decimal("2300.00"),
        estimated_fast_sale_price=Decimal("2024.00"),
        target_purchase_price=Decimal("1400.00"),
        estimated_transfer_cost=Decimal("125.70"),
        estimated_tax=Decimal("70.00"),
        estimated_repair_min=Decimal("0.00"),
        estimated_repair_max=Decimal("0.00"),
        estimated_preparation_cost=Decimal("200.00"),
        estimated_total_cost_min=Decimal("2075.70"),
        estimated_total_cost_max=Decimal("2075.70"),
        estimated_margin_min=Decimal("-51.70"),
        estimated_margin_max=Decimal("-51.70"),
        estimated_roi_min=Decimal("-2.49"),
        estimated_roi_max=Decimal("-2.49"),
        confidence_level=ConfidenceLevel.LOW,
        seller_pressure_level=SellerPressureLevel.LOW,
        seller_pressure_reasons=["Publicación reciente"],
        created_at=now,
        updated_at=now,
    )
    op.listing = None
    op.vehicle = None
    op.score = None
    return op


@pytest.mark.asyncio
async def test_list_and_create_profiles() -> None:
    client = _client(_ctx(UserRole.OWNER))
    pid = uuid4()
    p = ScoringProfile(
        id=pid,
        name="Perfil Test",
        slug="perfil-test",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    v = ScoringProfileVersion(
        id=uuid4(),
        profile_id=pid,
        version_number=1,
        weights=dict(DEFAULT_SCORING_WEIGHTS),
        config={},
        is_immutable=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    p.versions = [v]

    with patch("app.scoring.service.ScoringService.list_profiles", return_value=[p]):
        res = await client.get("/api/v1/scoring/profiles")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["name"] == "Perfil Test"

    with patch("app.scoring.service.ScoringService.create_profile", return_value=p):
        res_c = await client.post(
            "/api/v1/scoring/profiles",
            json={"name": "Perfil Test", "slug": "perfil-test"},
        )
        assert res_c.status_code == 201


@pytest.mark.asyncio
async def test_opportunities_endpoints_flow() -> None:
    client = _client(_ctx(UserRole.OWNER))
    op = _fake_opportunity()

    # List opportunities
    with patch("app.scoring.service.ScoringService.list_opportunities", return_value=([op], 1)):
        res = await client.get("/api/v1/opportunities")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    # Get opportunity
    with patch("app.scoring.service.ScoringService.get_opportunity", return_value=op):
        res_g = await client.get(f"/api/v1/opportunities/{op.id}")
        assert res_g.status_code == 200
        assert res_g.json()["id"] == str(op.id)

    # Patch status
    with patch("app.scoring.service.ScoringService.update_opportunity_status", return_value=op):
        res_p = await client.patch(
            f"/api/v1/opportunities/{op.id}/status",
            json={"status": "ANALYZING", "notes": "En estudio"},
        )
        assert res_p.status_code == 200

    # Evaluate listing
    with patch("app.scoring.service.ScoringService.evaluate_listing", return_value=op):
        res_ev = await client.post(f"/api/v1/opportunities/evaluate/listing/{uuid4()}")
        assert res_ev.status_code == 200

    # Evaluate vehicle
    with patch("app.scoring.service.ScoringService.evaluate_vehicle", return_value=op):
        res_ev_v = await client.post(f"/api/v1/opportunities/evaluate/vehicle/{uuid4()}")
        assert res_ev_v.status_code == 200


@pytest.mark.asyncio
async def test_viewer_rbac_denial() -> None:
    client = _client(_ctx(UserRole.VIEWER))

    # Mutation endpoints should return 403 Forbidden for VIEWER
    res1 = await client.post("/api/v1/scoring/profiles", json={"name": "P", "slug": "p"})
    assert res1.status_code == 403

    res2 = await client.patch(
        f"/api/v1/opportunities/{uuid4()}/status", json={"status": "VALIDATED"}
    )
    assert res2.status_code == 403

    res3 = await client.post(f"/api/v1/opportunities/evaluate/listing/{uuid4()}")
    assert res3.status_code == 403
