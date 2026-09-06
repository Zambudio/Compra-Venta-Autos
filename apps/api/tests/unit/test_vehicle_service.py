from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import app.models  # noqa: F401
import pytest
from app.listings.models import ListingSnapshot, VehicleListing
from app.listings.vocab import EntryChannel, FuelType, ListingStatus, SellerType, Transmission
from app.vehicles.errors import (
    MatchCandidateAlreadyDecidedError,
    MatchCandidateNotFoundError,
    VehicleNotFoundError,
)
from app.vehicles.models import Vehicle, VehicleMatchCandidate
from app.vehicles.service import VehicleService
from app.vehicles.vocab import MatchCandidateStatus


def _make_listing(
    *,
    vehicle_id=None,
    brand="SEAT",
    model="Ibiza",
    year=2015,
    mileage_km=120000,
    price_amount=Decimal("4500.00"),
) -> VehicleListing:
    listing = VehicleListing()
    listing.id = uuid4()
    listing.source_id = uuid4()
    listing.external_id = f"ext-{uuid4().hex[:6]}"
    listing.vehicle_id = vehicle_id
    listing.brand = brand
    listing.model = model
    listing.year = year
    listing.mileage_km = mileage_km
    listing.price_amount = price_amount
    listing.price_currency = "EUR"
    listing.fuel_type = FuelType.DIESEL
    listing.transmission = Transmission.MANUAL
    listing.seller_type = SellerType.PRIVATE
    listing.entry_channel = EntryChannel.MOCK_SYNC
    listing.status = ListingStatus.ACTIVE
    listing.payload_hash = "abc"
    listing.image_urls = []
    listing.generation = "IV"
    listing.trim = "1.6 TDI"
    listing.engine_code = "CAYB"
    listing.power_kw = 66
    listing.province = "Madrid"
    listing.description = "Buen coche"
    listing.snapshots = []
    return listing


@pytest.mark.unit
@pytest.mark.asyncio
async def test_confirm_match_creates_new_vehicle_when_neither_has_one() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    candidate = VehicleMatchCandidate()
    candidate.id = uuid4()
    candidate.listing_a = _make_listing()
    candidate.listing_b = _make_listing()
    candidate.status = MatchCandidateStatus.PENDING
    candidate.confidence_score = Decimal("0.850")

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = candidate
    session.execute.return_value = result_mock

    user_id = uuid4()
    updated = await VehicleService.confirm_match(session, candidate.id, user_id)

    assert updated.status == MatchCandidateStatus.CONFIRMED
    assert updated.decided_by_user_id == user_id
    assert updated.listing_a.vehicle_id is not None
    assert updated.listing_a.vehicle_id == updated.listing_b.vehicle_id
    assert session.add.call_count == 2  # new_vehicle + audit event


@pytest.mark.unit
@pytest.mark.asyncio
async def test_confirm_match_reuses_vehicle_when_one_exists() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    existing_vid = uuid4()
    existing_vehicle = Vehicle(
        id=existing_vid,
        brand="SEAT",
        model="Ibiza",
        year=2015,
        fuel_type=FuelType.DIESEL,
        transmission=Transmission.MANUAL,
        first_listed_at=datetime.now(UTC),
        listing_count=1,
    )

    candidate = VehicleMatchCandidate()
    candidate.id = uuid4()
    candidate.listing_a = _make_listing(vehicle_id=existing_vid)
    candidate.listing_b = _make_listing(vehicle_id=None)
    candidate.status = MatchCandidateStatus.PENDING
    candidate.confidence_score = Decimal("0.850")

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = candidate
    session.execute.return_value = result_mock
    session.get.return_value = existing_vehicle

    user_id = uuid4()
    updated = await VehicleService.confirm_match(session, candidate.id, user_id)

    assert updated.status == MatchCandidateStatus.CONFIRMED
    assert updated.listing_b.vehicle_id == existing_vid
    assert existing_vehicle.listing_count == 2
    assert session.add.call_count == 1  # only audit event


@pytest.mark.unit
@pytest.mark.asyncio
async def test_confirm_match_both_have_existing_different_vehicles_merges() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    v1_id = uuid4()
    v2_id = uuid4()
    v1 = Vehicle(
        id=v1_id,
        brand="SEAT",
        model="Ibiza",
        year=2015,
        fuel_type=FuelType.DIESEL,
        transmission=Transmission.MANUAL,
        first_listed_at=datetime.now(UTC),
        listing_count=1,
    )
    v2 = Vehicle(
        id=v2_id,
        brand="SEAT",
        model="Ibiza",
        year=2015,
        fuel_type=FuelType.DIESEL,
        transmission=Transmission.MANUAL,
        first_listed_at=datetime.now(UTC),
        listing_count=1,
    )

    candidate = VehicleMatchCandidate()
    candidate.id = uuid4()
    l_a = _make_listing(vehicle_id=v1_id)
    l_b = _make_listing(vehicle_id=v2_id)
    candidate.listing_a = l_a
    candidate.listing_b = l_b
    candidate.status = MatchCandidateStatus.PENDING
    candidate.confidence_score = Decimal("0.900")

    cand_mock = MagicMock()
    cand_mock.scalar_one_or_none.return_value = candidate

    sec_listings_mock = MagicMock()
    sec_listings_mock.scalars.return_value.all.return_value = [l_b]

    session.execute.side_effect = [cand_mock, sec_listings_mock]

    async def _mock_get(entity_cls, entity_id):
        if entity_id == v1_id:
            return v1
        if entity_id == v2_id:
            return v2
        return None

    session.get.side_effect = _mock_get

    user_id = uuid4()
    updated = await VehicleService.confirm_match(session, candidate.id, user_id)

    assert updated.status == MatchCandidateStatus.CONFIRMED
    assert l_b.vehicle_id == v1_id
    assert v1.listing_count == 2
    session.delete.assert_called_once_with(v2)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_confirm_match_not_found_raises() -> None:
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    session.execute.return_value = result_mock

    with pytest.raises(MatchCandidateNotFoundError):
        await VehicleService.confirm_match(session, uuid4(), uuid4())


@pytest.mark.unit
@pytest.mark.asyncio
async def test_confirm_match_already_decided_raises_conflict() -> None:
    session = AsyncMock()
    candidate = VehicleMatchCandidate()
    candidate.id = uuid4()
    candidate.status = MatchCandidateStatus.CONFIRMED

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = candidate
    session.execute.return_value = result_mock

    with pytest.raises(MatchCandidateAlreadyDecidedError):
        await VehicleService.confirm_match(session, candidate.id, uuid4())


@pytest.mark.unit
@pytest.mark.asyncio
async def test_reject_match_success() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    candidate = VehicleMatchCandidate()
    candidate.id = uuid4()
    candidate.status = MatchCandidateStatus.PENDING

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = candidate
    session.execute.return_value = result_mock

    user_id = uuid4()
    updated = await VehicleService.reject_match(session, candidate.id, user_id)

    assert updated.status == MatchCandidateStatus.REJECTED
    assert updated.decided_by_user_id == user_id
    assert session.add.call_count == 1  # audit event


@pytest.mark.unit
@pytest.mark.asyncio
async def test_reject_match_not_found_raises() -> None:
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    session.execute.return_value = result_mock

    with pytest.raises(MatchCandidateNotFoundError):
        await VehicleService.reject_match(session, uuid4(), uuid4())


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_match_candidates_creates_matches() -> None:
    session = AsyncMock()
    session.add = MagicMock()

    l1 = _make_listing(brand="SEAT", model="Leon", year=2018, mileage_km=90000)
    l2 = _make_listing(brand="SEAT", model="Leon", year=2018, mileage_km=91000)

    exec1 = MagicMock()
    exec1.scalars.return_value.all.return_value = [l1]

    exec2 = MagicMock()
    exec2.scalars.return_value.all.return_value = [l2]

    exec3 = MagicMock()
    exec3.scalar_one_or_none.return_value = None  # no existing candidate

    session.execute.side_effect = [exec1, exec2, exec3]

    created = await VehicleService.generate_match_candidates(
        session, new_listing_ids=[l1.id], min_confidence=Decimal("0.60")
    )
    assert created == 1
    assert session.add.call_count == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_match_candidates_no_listings() -> None:
    session = AsyncMock()
    exec1 = MagicMock()
    exec1.scalars.return_value.all.return_value = []
    session.execute.return_value = exec1

    created = await VehicleService.generate_match_candidates(session)
    assert created == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_match_candidates() -> None:
    session = AsyncMock()
    candidate = VehicleMatchCandidate()
    candidate.id = uuid4()
    candidate.confidence_score = Decimal("0.850")

    count_res = MagicMock()
    count_res.scalar_one.return_value = 1

    items_res = MagicMock()
    items_res.scalars.return_value.all.return_value = [candidate]

    session.execute.side_effect = [count_res, items_res]

    items, total = await VehicleService.list_match_candidates(session)
    assert total == 1
    assert len(items) == 1
    assert items[0].id == candidate.id


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_vehicle_detail_and_history() -> None:
    session = AsyncMock()
    v = Vehicle(
        id=uuid4(),
        brand="SEAT",
        model="Ibiza",
        year=2015,
        fuel_type=FuelType.DIESEL,
        transmission=Transmission.MANUAL,
        first_listed_at=datetime.now(UTC),
        listing_count=1,
    )
    listing = _make_listing(vehicle_id=v.id, price_amount=Decimal("5000.00"))
    snap1 = ListingSnapshot(
        observed_at=datetime(2026, 1, 1, tzinfo=UTC),
        price_amount=Decimal("5500.00"),
        price_currency="EUR",
        mileage_km=100000,
        status=ListingStatus.ACTIVE,
    )
    snap2 = ListingSnapshot(
        observed_at=datetime(2026, 1, 10, tzinfo=UTC),
        price_amount=Decimal("5000.00"),
        price_currency="EUR",
        mileage_km=100000,
        status=ListingStatus.ACTIVE,
    )
    listing.snapshots = [snap1, snap2]
    v.listings = [listing]
    v.estimates = []

    res_mock = MagicMock()
    res_mock.scalar_one_or_none.return_value = v
    session.execute.return_value = res_mock

    detail = await VehicleService.get_vehicle_detail(session, v.id)
    assert detail.id == v.id

    history = await VehicleService.get_vehicle_history(session, v.id)
    assert history.lowest_observed_price == Decimal("5000.00")
    assert history.highest_observed_price == Decimal("5500.00")
    assert history.days_on_market == 9
    assert history.total_price_changes == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_vehicle_detail_not_found() -> None:
    session = AsyncMock()
    res_mock = MagicMock()
    res_mock.scalar_one_or_none.return_value = None
    session.execute.return_value = res_mock

    with pytest.raises(VehicleNotFoundError):
        await VehicleService.get_vehicle_detail(session, uuid4())


@pytest.mark.unit
@pytest.mark.asyncio
async def test_compute_and_save_market_estimate() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    v = Vehicle(
        id=uuid4(),
        brand="SEAT",
        model="Ibiza",
        year=2015,
        fuel_type=FuelType.DIESEL,
        transmission=Transmission.MANUAL,
        first_listed_at=datetime.now(UTC),
        listing_count=1,
    )
    l_v = _make_listing(
        vehicle_id=v.id,
        brand="SEAT",
        model="Ibiza",
        year=2015,
        mileage_km=100000,
        price_amount=Decimal("5000"),
    )
    v.listings = [l_v]
    v.estimates = []

    res_veh = MagicMock()
    res_veh.scalar_one_or_none.return_value = v

    # Pool de 4 comparables
    pool_listings = [
        _make_listing(
            brand="SEAT", model="Ibiza", year=2015, mileage_km=95000, price_amount=Decimal("4800")
        ),
        _make_listing(
            brand="SEAT", model="Ibiza", year=2015, mileage_km=105000, price_amount=Decimal("5200")
        ),
        _make_listing(
            brand="SEAT", model="Ibiza", year=2015, mileage_km=102000, price_amount=Decimal("5100")
        ),
        _make_listing(
            brand="SEAT", model="Ibiza", year=2015, mileage_km=98000, price_amount=Decimal("4900")
        ),
    ]
    res_pool = MagicMock()
    res_pool.scalars.return_value.all.return_value = pool_listings

    session.execute.side_effect = [res_veh, res_pool]

    est = await VehicleService.compute_and_save_market_estimate(session, v.id, min_comparables=3)
    assert est.vehicle_id == v.id
    assert est.number_of_comparables == 4
    assert est.estimated_amount == Decimal("5000.00")  # median de 4800, 4900, 5100, 5200 = 5000
    assert session.add.call_count == 1
