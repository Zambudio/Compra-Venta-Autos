"""Test ingestion flow: normalization and persistence of listings.

Mock/stub test data replaces the removed MockConnector from production.
This tests ListingService, not any connector specifically.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.connectors.filters import ConnectorSearchFilter
from app.connectors.schemas import ConnectorSearchPage, RawListing
from app.listings.models import ListingSnapshot, RawListingPayload, VehicleListing
from app.listings.service import ListingService
from app.sources.models import Source
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


def _stub_listings() -> list[RawListing]:
    """Return stub test listings for ingestion tests.

    Replaces MockConnector data. These are minimal but valid listings.
    """
    return [
        RawListing(
            source_key="manual",
            external_id="test-seat-1",
            url="https://example.local/test-seat-1",
            retrieved_at=datetime.now(UTC),
            connector_version="test-v1",
            payload={
                "id": "test-seat-1",
                "brand": "SEAT",
                "model": "Ibiza",
                "year": 2014,
                "precio": 2800,
                "kms": 168000,
                "fuel": "DIESEL",
                "transmission": "manual",
                "province": "Murcia",
            },
        ),
        RawListing(
            source_key="manual",
            external_id="test-dacia-1",
            url="https://example.local/test-dacia-1",
            retrieved_at=datetime.now(UTC),
            connector_version="test-v1",
            payload={
                "id": "test-dacia-1",
                "brand": "Dacia",
                "model": "Sandero",
                "year": 2018,
                "precio": 6500,
                "kms": 85000,
                "fuel": "GASOLINE",
                "transmission": "manual",
                "province": "Madrid",
            },
        ),
        RawListing(
            source_key="manual",
            external_id="test-seat-2",
            url="https://example.local/test-seat-2",
            retrieved_at=datetime.now(UTC),
            connector_version="test-v1",
            payload={
                "id": "test-seat-2",
                "brand": "SEAT",
                "model": "Cordoba",
                "year": 2010,
                "precio": 1800,
                "kms": 210000,
                "fuel": "DIESEL",
                "transmission": "manual",
                "province": "Barcelona",
            },
        ),
    ]


async def _manual_source(session: AsyncSession) -> Source:
    """Get the manual (user entry) source."""
    return (await session.execute(select(Source).where(Source.key == "manual"))).scalar_one()


async def _count(session: AsyncSession, model: type) -> int:
    """Count rows in a model."""
    return (await session.execute(select(func.count()).select_from(model))).scalar_one()


async def test_full_sync_persists_listings_payloads_and_snapshots(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Test that ingesting raw listings creates all related records."""
    items = _stub_listings()

    async with session_factory() as session:
        source = await _manual_source(session)
        service = ListingService(session)
        for item in items:
            await service.ingest_raw(item, source)
        await session.commit()

        assert await _count(session, VehicleListing) == len(items)
        assert await _count(session, RawListingPayload) == len(items)
        assert await _count(session, ListingSnapshot) == len(items)


async def test_re_sync_is_idempotent_and_preserves_state(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Test that re-ingesting the same listings does not create duplicates."""
    items = _stub_listings()

    async with session_factory() as session:
        source = await _manual_source(session)
        service = ListingService(session)

        # First ingest
        for item in items:
            await service.ingest_raw(item, source)
        await session.commit()

        first_count = await _count(session, VehicleListing)
        assert first_count == len(items)

        # Re-ingest same items
        outcomes = [await service.ingest_raw(item, source) for item in items]
        await session.commit()

        # Should not create new listings
        second_count = await _count(session, VehicleListing)
        assert second_count == first_count
        assert all(o.created is False and o.updated is False for o in outcomes)


async def test_price_change_creates_new_snapshot(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Test that updating a listing's price creates a new snapshot."""
    original_item = _stub_listings()[0]

    async with session_factory() as session:
        source = await _manual_source(session)
        service = ListingService(session)

        # First ingest
        first = await service.ingest_raw(original_item, source)
        await session.commit()

        # Modify price
        cheaper_payload = dict(original_item.payload)
        cheaper_payload["precio"] = int(cheaper_payload["precio"]) - 500
        cheaper = original_item.model_copy(update={"payload": cheaper_payload})

        # Re-ingest with new price
        second = await service.ingest_raw(cheaper, source)
        await session.commit()

        assert second.updated is True
        assert second.snapshot_created is True

        # Verify snapshots
        snapshots = (
            (
                await session.execute(
                    select(ListingSnapshot.price_amount)
                    .where(ListingSnapshot.listing_id == first.listing_id)
                    .order_by(ListingSnapshot.observed_at)
                )
            )
            .scalars()
            .all()
        )
        assert len(snapshots) == 2
        assert snapshots[1] == Decimal(cheaper_payload["precio"])
