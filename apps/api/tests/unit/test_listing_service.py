from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from app.connectors.schemas import RawListing
from app.listings.models import VehicleListing
from app.listings.service import IngestDecision, ListingService, decide_ingest
from app.listings.vocab import (
    EntryChannel,
    FuelType,
    ListingStatus,
    ProviderKind,
    SellerType,
    Transmission,
)
from app.sources.models import Source
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.unit


def _decision(**kwargs: object) -> IngestDecision:
    defaults: dict[str, object] = {
        "listing_exists": True,
        "payload_already_seen": False,
        "existing_price": Decimal("3000"),
        "existing_mileage": 100000,
        "existing_description_hash": "abc",
        "new_price": Decimal("3000"),
        "new_mileage": 100000,
        "new_description_hash": "abc",
    }
    defaults.update(kwargs)
    return decide_ingest(**defaults)  # type: ignore[arg-type]


def test_decide_ingest_creates_when_listing_is_new() -> None:
    decision = _decision(listing_exists=False)

    assert decision.action == "create"
    assert decision.write_snapshot is True


def test_decide_ingest_marks_seen_when_payload_already_stored() -> None:
    decision = _decision(payload_already_seen=True, new_price=Decimal("2500"))

    assert decision.action == "seen"
    assert decision.write_snapshot is False


def test_decide_ingest_updates_without_snapshot_when_nothing_changed() -> None:
    decision = _decision()

    assert decision.action == "update"
    assert decision.write_snapshot is False


@pytest.mark.parametrize(
    "change",
    [
        {"new_price": Decimal("2500")},
        {"new_mileage": 112000},
        {"new_description_hash": "zzz"},
    ],
)
def test_decide_ingest_writes_snapshot_on_relevant_change(change: dict[str, object]) -> None:
    decision = _decision(**change)

    assert decision.action == "update"
    assert decision.write_snapshot is True


@pytest.mark.asyncio
async def test_search_builds_page_from_repository_rows() -> None:
    from app.listings.repository import ListingRepository
    from app.search.schemas import SearchFilter

    listing = _existing_listing(id=uuid4())
    with patch.object(
        ListingRepository, "search", AsyncMock(return_value=([(listing, "mock")], 1))
    ):
        page = await ListingService(AsyncMock(spec=AsyncSession)).search(
            SearchFilter(page=1, page_size=20)
        )

    assert page.total == 1
    assert page.has_more is False
    assert page.items[0].source_key == "mock"


@pytest.mark.asyncio
async def test_get_detail_raises_when_missing() -> None:
    from app.listings.repository import ListingRepository
    from app.listings.service import ListingNotFoundError

    with patch.object(ListingRepository, "get_with_snapshots", AsyncMock(return_value=None)):
        with pytest.raises(ListingNotFoundError):
            await ListingService(AsyncMock(spec=AsyncSession)).get_detail(uuid4())


@pytest.mark.asyncio
async def test_ingest_raw_creates_listing_payload_and_snapshot() -> None:
    db = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    source = Source(id=uuid4(), key="mock", name="Mock", provider_kind=ProviderKind.MOCK)
    raw = RawListing(
        source_key="mock",
        external_id="mock-0001",
        url="https://mock.local/1",
        retrieved_at=datetime(2026, 9, 1, tzinfo=UTC),
        connector_version="mock-catalog-v1",
        payload={
            "external_id": "mock-0001",
            "marca": "Seat",
            "modelo": "Ibiza",
            "anio": 2013,
            "km": 168000,
            "precio": 2800,
            "combustible": "Diésel",
            "vendedor": "particular",
        },
    )

    outcome = await ListingService(db).ingest_raw(raw, source)

    assert outcome.created is True
    assert outcome.snapshot_created is True
    # listing + raw payload + snapshot
    assert db.add.call_count == 3
    added_types = {type(call.args[0]).__name__ for call in db.add.call_args_list}
    assert added_types == {"VehicleListing", "RawListingPayload", "ListingSnapshot"}


def _existing_listing(**overrides: object) -> VehicleListing:
    defaults: dict[str, object] = {
        "id": uuid4(),
        "source_id": uuid4(),
        "external_id": "mock-0001",
        "brand": "SEAT",
        "model": "Ibiza",
        "fuel_type": FuelType.DIESEL,
        "transmission": Transmission.MANUAL,
        "seller_type": SellerType.PRIVATE,
        "status": ListingStatus.ACTIVE,
        "year": 2013,
        "mileage_km": 168000,
        "price_amount": Decimal("2800"),
        "price_currency": "EUR",
        "description": None,
        "image_urls": [],
        "payload_hash": "old-hash",
        "url": None,
        "generation": None,
        "trim": None,
        "engine_code": None,
        "power_kw": None,
        "location": None,
        "province": "Murcia",
        "first_seen_at": datetime(2026, 7, 1, tzinfo=UTC),
        "last_seen_at": datetime(2026, 8, 1, tzinfo=UTC),
        "published_at": None,
    }
    defaults.update(overrides)
    return VehicleListing(**defaults)


@pytest.mark.asyncio
async def test_ingest_raw_marks_seen_when_payload_hash_already_stored() -> None:
    db = AsyncMock(spec=AsyncSession)
    listing = _existing_listing()
    get_result = MagicMock()
    get_result.scalar_one_or_none.return_value = listing
    payload_result = MagicMock()
    payload_result.first.return_value = ("payload-id",)
    db.execute.side_effect = [get_result, payload_result]

    source = Source(id=uuid4(), key="mock", name="Mock", provider_kind=ProviderKind.MOCK)
    raw = RawListing(
        source_key="mock",
        external_id="mock-0001",
        url=None,
        retrieved_at=datetime(2026, 9, 5, tzinfo=UTC),
        connector_version="mock-catalog-v1",
        payload={
            "external_id": "mock-0001",
            "marca": "Seat",
            "modelo": "Ibiza",
            "anio": 2013,
            "km": 168000,
            "precio": 2800,
            "combustible": "Diésel",
            "vendedor": "particular",
        },
    )

    outcome = await ListingService(db).ingest_raw(raw, source)

    assert outcome.created is False
    assert outcome.updated is False
    assert outcome.snapshot_created is False
    db.add.assert_not_called()
    assert listing.last_seen_at == datetime(2026, 9, 5, tzinfo=UTC)


@pytest.mark.asyncio
async def test_ingest_raw_updates_and_snapshots_on_price_change() -> None:
    db = AsyncMock(spec=AsyncSession)
    listing = _existing_listing(price_amount=Decimal("2800"))
    get_result = MagicMock()
    get_result.scalar_one_or_none.return_value = listing
    payload_result = MagicMock()
    payload_result.first.return_value = None
    db.execute.side_effect = [get_result, payload_result]

    source = Source(id=uuid4(), key="mock", name="Mock", provider_kind=ProviderKind.MOCK)
    raw = RawListing(
        source_key="mock",
        external_id="mock-0001",
        url=None,
        retrieved_at=datetime(2026, 9, 5, tzinfo=UTC),
        connector_version="mock-catalog-v1",
        payload={
            "external_id": "mock-0001",
            "marca": "Seat",
            "modelo": "Ibiza",
            "anio": 2013,
            "km": 168000,
            "precio": 2500,
            "combustible": "Diésel",
            "vendedor": "particular",
        },
    )

    outcome = await ListingService(db).ingest_raw(raw, source)

    assert outcome.updated is True
    assert outcome.snapshot_created is True
    assert listing.price_amount == Decimal("2500")
    added_types = {type(call.args[0]).__name__ for call in db.add.call_args_list}
    assert added_types == {"RawListingPayload", "ListingSnapshot"}


@pytest.mark.asyncio
async def test_ingest_raw_uses_manual_entry_channel_for_manual_source() -> None:
    db = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    source = Source(id=uuid4(), key="manual", name="Manual", provider_kind=ProviderKind.MANUAL)
    raw = RawListing(
        source_key="manual",
        external_id="manual-xyz",
        url=None,
        retrieved_at=datetime(2026, 9, 1, tzinfo=UTC),
        connector_version="manual-entry-v1",
        payload={
            "external_id": "manual-xyz",
            "marca": "Dacia",
            "modelo": "Sandero",
            "anio": 2016,
            "km": 90000,
            "precio": 5200,
            "combustible": "Gasolina",
            "vendedor": "particular",
        },
    )

    await ListingService(db).ingest_raw(raw, source)

    listing = next(
        call.args[0]
        for call in db.add.call_args_list
        if type(call.args[0]).__name__ == "VehicleListing"
    )
    assert listing.entry_channel is EntryChannel.MANUAL_ENTRY
