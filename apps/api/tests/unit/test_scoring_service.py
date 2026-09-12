"""Tests unitarios para ScoringService con AsyncMock sin dependencias externas."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import app.models  # noqa: F401
import pytest
from app.knowledge.schemas import ReliabilityLookupResponse
from app.knowledge.vocab import ClassificationStatus
from app.listings.models import ListingSnapshot, VehicleListing
from app.listings.vocab import FuelType, Transmission
from app.scoring.errors import (
    OpportunityNotFoundError,
    ScoringProfileNotFoundError,
    ScoringProfileSlugAlreadyExistsError,
    ScoringProfileVersionNotFoundError,
    TargetNotFoundError,
)
from app.scoring.models import Opportunity, ScoringProfile, ScoringProfileVersion
from app.scoring.schemas import (
    ScoringProfileCreate,
    ScoringProfileVersionCreate,
)
from app.scoring.service import DEFAULT_PROFILE_SLUG, ScoringService
from app.scoring.vocab import (
    DEFAULT_SCORING_WEIGHTS,
    ConfidenceLevel,
    OpportunityStatus,
    SellerPressureLevel,
)
from app.vehicles.models import MarketEstimate, Vehicle

pytestmark = pytest.mark.unit


def _scalar_result(value: object) -> MagicMock:
    mock = MagicMock()
    mock.scalar_one_or_none.return_value = value
    mock.scalar_one.return_value = value
    if isinstance(value, list):
        mock.scalars.return_value.all.return_value = value
    elif value is not None:
        mock.scalars.return_value.all.return_value = [value]
    else:
        mock.scalars.return_value.all.return_value = []
    return mock


@pytest.mark.asyncio
async def test_get_or_create_default_profile() -> None:
    session = AsyncMock()
    session.add = MagicMock()

    # Caso 1: Perfil ya existe con versiones
    existing_profile = ScoringProfile(
        id=uuid4(),
        name="Oportunidad Reventa Rápida",
        slug=DEFAULT_PROFILE_SLUG,
        is_active=True,
    )
    v1 = ScoringProfileVersion(
        id=uuid4(),
        profile_id=existing_profile.id,
        version_number=1,
        weights=dict(DEFAULT_SCORING_WEIGHTS),
        config={},
        is_immutable=True,
    )
    existing_profile.versions = [v1]

    session.execute.return_value = _scalar_result(existing_profile)
    p, v = await ScoringService.get_or_create_default_profile(session)
    assert p.slug == DEFAULT_PROFILE_SLUG
    assert v.version_number == 1

    # Caso 2: No existe -> lo crea
    session.execute.return_value = _scalar_result(None)
    session.refresh = AsyncMock()
    p_new, v_new = await ScoringService.get_or_create_default_profile(session)
    assert p_new.slug == DEFAULT_PROFILE_SLUG
    assert v_new.version_number == 1
    assert session.add.call_count >= 2


@pytest.mark.asyncio
async def test_profile_crud_and_errors() -> None:
    session = AsyncMock()
    session.add = MagicMock()

    # Create profile
    session.execute.return_value = _scalar_result(None)
    session.refresh = AsyncMock()
    dto = ScoringProfileCreate(
        name="Perfil Conservador",
        slug="perfil-conservador",
        description="Estrategia conservadora",
    )
    created = await ScoringService.create_profile(session, dto)
    assert created.name == "Perfil Conservador"
    assert created.slug == "perfil-conservador"

    # Duplicate slug
    session.execute.return_value = _scalar_result(created)
    with pytest.raises(ScoringProfileSlugAlreadyExistsError):
        await ScoringService.create_profile(session, dto)

    # Get profile not found
    session.execute.return_value = _scalar_result(None)
    with pytest.raises(ScoringProfileNotFoundError):
        await ScoringService.get_profile(session, uuid4())

    # Get version not found
    session.execute.return_value = _scalar_result(None)
    with pytest.raises(ScoringProfileVersionNotFoundError):
        await ScoringService.get_profile_version(session, uuid4())


@pytest.mark.asyncio
async def test_create_profile_version() -> None:
    session = AsyncMock()
    session.add = MagicMock()

    profile = ScoringProfile(
        id=uuid4(),
        name="Perfil Dinámico",
        slug="perfil-dinamico",
        is_active=True,
    )
    v1 = ScoringProfileVersion(
        id=uuid4(),
        profile_id=profile.id,
        version_number=1,
        weights=dict(DEFAULT_SCORING_WEIGHTS),
        config={},
    )
    profile.versions = [v1]

    session.execute.return_value = _scalar_result(profile)
    v_new = await ScoringService.create_profile_version(
        session,
        profile.id,
        ScoringProfileVersionCreate(weights=dict(DEFAULT_SCORING_WEIGHTS)),
    )
    assert v_new.version_number == 2
    session.add.assert_called_once()


@pytest.mark.asyncio
async def test_evaluate_listing_full_flow() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()

    # Mock del listing
    now = datetime.now(UTC)
    listing_id = uuid4()
    listing = VehicleListing(
        id=listing_id,
        source_id=uuid4(),
        external_id="mock-101",
        brand="SEAT",
        model="Ibiza",
        year=2010,
        mileage_km=145000,
        price_amount=Decimal("1700.00"),
        price_currency="EUR",
        fuel_type=FuelType.DIESEL,
        transmission=Transmission.MANUAL,
        published_at=now - timedelta(days=20),
        last_seen_at=now,
        description="ITV en vigor, distribución recién cambiada con factura.",
    )
    snap1 = ListingSnapshot(
        id=uuid4(),
        listing_id=listing_id,
        price_amount=Decimal("1900.00"),
        observed_at=now - timedelta(days=20),
    )
    listing.snapshots = [snap1]
    listing.vehicle_id = None

    # Mock de versión de perfil
    profile = ScoringProfile(
        id=uuid4(),
        name="Oportunidad Reventa Rápida",
        slug=DEFAULT_PROFILE_SLUG,
    )
    version = ScoringProfileVersion(
        id=uuid4(),
        profile_id=profile.id,
        version_number=1,
        weights=dict(DEFAULT_SCORING_WEIGHTS),
        config={
            "fast_sale_discount_ratio": 0.88,
            "preparation_cost_default": 200.0,
            "transfer_tax_ratio": 0.04,
            "transfer_fee_dgt": 55.70,
            "target_roi_min": 25.0,
        },
    )
    profile.versions = [version]

    # Mock de MarketEstimate
    market_estimate = MarketEstimate(
        id=uuid4(),
        listing_id=listing_id,
        estimated_amount=Decimal("2400.00"),
        low_amount=Decimal("2100.00"),
        high_amount=Decimal("2700.00"),
        number_of_comparables=12,
        confidence_score=Decimal("0.80"),
    )

    # Mock de KnowledgeBase
    kb_response = ReliabilityLookupResponse(
        brand="SEAT",
        model="Ibiza",
        classification=ClassificationStatus.WHITELIST,
        issues_count=0,
        total_estimated_repair_min=Decimal("0.00"),
        total_estimated_repair_max=Decimal("0.00"),
        has_recalls=False,
    )

    def mock_execute(stmt: object) -> MagicMock:
        s_str = str(stmt).lower()
        if "from vehicle_listings" in s_str:
            return _scalar_result(listing)
        if "from scoring_profiles" in s_str:
            return _scalar_result(profile)
        if "from market_estimates" in s_str:
            return _scalar_result(market_estimate)
        if "from opportunities" in s_str:
            return _scalar_result(None)  # no opportunity yet
        return _scalar_result(None)

    session.execute.side_effect = mock_execute

    with patch(
        "app.scoring.service.KnowledgeService.lookup_vehicle_reliability",
        new_callable=AsyncMock,
        return_value=kb_response,
    ):
        op = await ScoringService.evaluate_listing(session, listing_id)

    assert op is not None
    assert op.asking_price == Decimal("1700.00")
    assert op.status == OpportunityStatus.IDENTIFIED
    assert op.estimated_fast_sale_price == Decimal("2100.00")
    assert op.confidence_level == ConfidenceLevel.MEDIUM
    assert op.seller_pressure_level == SellerPressureLevel.MEDIUM
    assert session.add.call_count >= 2  # OpportunityScore + Opportunity


@pytest.mark.asyncio
async def test_evaluate_vehicle_flow() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()

    vehicle_id = uuid4()
    now = datetime.now(UTC)
    vehicle = Vehicle(
        id=vehicle_id,
        brand="Volkswagen",
        model="Golf",
        year=2011,
        fuel_type=FuelType.DIESEL,
        transmission=Transmission.MANUAL,
    )
    listing = VehicleListing(
        id=uuid4(),
        vehicle_id=vehicle_id,
        source_id=uuid4(),
        external_id="golf-01",
        brand="Volkswagen",
        model="Golf",
        year=2011,
        price_amount=Decimal("2600.00"),
        fuel_type=FuelType.DIESEL,
        transmission=Transmission.MANUAL,
        published_at=now - timedelta(days=10),
        last_seen_at=now,
    )
    listing.snapshots = []
    vehicle.listings = [listing]

    def mock_execute(stmt: object) -> MagicMock:
        s_str = str(stmt).lower()
        if "from vehicles" in s_str:
            return _scalar_result(vehicle)
        if "from vehicle_listings" in s_str:
            return _scalar_result(listing)
        if "from scoring_profiles" in s_str:
            p = ScoringProfile(id=uuid4(), name="R", slug=DEFAULT_PROFILE_SLUG)
            v = ScoringProfileVersion(
                id=uuid4(),
                profile_id=p.id,
                version_number=1,
                weights=dict(DEFAULT_SCORING_WEIGHTS),
                config={},
            )
            p.versions = [v]
            return _scalar_result(p)
        if "from market_estimates" in s_str:
            return _scalar_result(None)
        if "from opportunities" in s_str:
            return _scalar_result(None)
        if "count(vehicle_mitigations.id)" in s_str:
            return _scalar_result(0)
        return _scalar_result(None)

    session.execute.side_effect = mock_execute

    kb_response = ReliabilityLookupResponse(
        brand="Volkswagen",
        model="Golf",
        classification=ClassificationStatus.UNKNOWN,
        issues_count=0,
    )

    with patch(
        "app.scoring.service.KnowledgeService.lookup_vehicle_reliability",
        new_callable=AsyncMock,
        return_value=kb_response,
    ):
        op = await ScoringService.evaluate_vehicle(session, vehicle_id)

    assert op is not None
    assert op.asking_price == Decimal("2600.00")


@pytest.mark.asyncio
async def test_opportunity_not_found_and_status_update() -> None:
    session = AsyncMock()
    session.execute.return_value = _scalar_result(None)

    with pytest.raises(OpportunityNotFoundError):
        await ScoringService.get_opportunity(session, uuid4())

    with pytest.raises(TargetNotFoundError):
        await ScoringService.evaluate_listing(session, uuid4())

    with pytest.raises(TargetNotFoundError):
        await ScoringService.evaluate_vehicle(session, uuid4())

    # Update status exitoso
    op = Opportunity(
        id=uuid4(),
        status=OpportunityStatus.IDENTIFIED,
        asking_price=Decimal("1500.00"),
    )
    session.execute.return_value = _scalar_result(op)
    updated = await ScoringService.update_opportunity_status(
        session, op.id, OpportunityStatus.VALIDATED, notes="Revisión exitosa"
    )
    assert updated.status == OpportunityStatus.VALIDATED
    assert updated.notes == "Revisión exitosa"


@pytest.mark.unit
def test_map_to_read_enrichment() -> None:
    now = datetime.now(UTC)
    listing = VehicleListing(
        id=uuid4(),
        source_id=uuid4(),
        external_id="test-1",
        brand="Ford",
        model="Focus",
        year=2009,
        mileage_km=178000,
        location="Valencia",
        province="Valencia",
        url="https://anuncio.com/123",
        fuel_type=FuelType.PETROL,
        transmission=Transmission.MANUAL,
    )
    op = Opportunity(
        id=uuid4(),
        listing_id=listing.id,
        status=OpportunityStatus.ANALYZING,
        currency="EUR",
        asking_price=Decimal("1950.00"),
        estimated_transfer_cost=Decimal("133.70"),
        estimated_tax=Decimal("78.00"),
        estimated_repair_min=Decimal("0.00"),
        estimated_repair_max=Decimal("0.00"),
        estimated_preparation_cost=Decimal("200.00"),
        estimated_total_cost_min=Decimal("2283.70"),
        estimated_total_cost_max=Decimal("2283.70"),
        confidence_level=ConfidenceLevel.LOW,
        seller_pressure_level=SellerPressureLevel.MEDIUM,
        seller_pressure_reasons=["25 días publicado"],
        created_at=now,
        updated_at=now,
    )
    op.listing = listing
    op.vehicle = None
    op.score = None

    read_dto = ScoringService.map_to_read(op)
    assert read_dto.title == "Ford Focus"
    assert read_dto.brand == "Ford"
    assert read_dto.model == "Focus"
    assert read_dto.year == 2009
    assert read_dto.city == "Valencia"
    assert read_dto.external_url == "https://anuncio.com/123"
    assert read_dto.fuel_type == "PETROL"
