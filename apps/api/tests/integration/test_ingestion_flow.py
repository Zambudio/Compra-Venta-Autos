from __future__ import annotations

from decimal import Decimal

import pytest
from app.connectors.filters import ConnectorSearchFilter
from app.connectors.mock.connector import MockConnector
from app.listings.models import ListingSnapshot, RawListingPayload, VehicleListing
from app.listings.service import ListingService
from app.sources.models import Source
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _mock_source(session: AsyncSession) -> Source:
    return (await session.execute(select(Source).where(Source.key == "mock"))).scalar_one()


async def _count(session: AsyncSession, model: type) -> int:
    return (await session.execute(select(func.count()).select_from(model))).scalar_one()


async def test_full_mock_sync_persists_listings_payloads_and_snapshots(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    page = await MockConnector(latency_enabled=False, faults_enabled=False).search(
        ConnectorSearchFilter(page_size=100)
    )

    async with session_factory() as session:
        source = await _mock_source(session)
        service = ListingService(session)
        for item in page.items:
            await service.ingest_raw(item, source)
        await session.commit()

        assert await _count(session, VehicleListing) == page.total
        assert await _count(session, RawListingPayload) == page.total
        assert await _count(session, ListingSnapshot) == page.total


async def test_re_sync_is_idempotent_and_advances_last_seen(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    connector = MockConnector(latency_enabled=False, faults_enabled=False)
    page = await connector.search(ConnectorSearchFilter(brand="Seat", page_size=100))

    async with session_factory() as session:
        source = await _mock_source(session)
        service = ListingService(session)
        for item in page.items:
            await service.ingest_raw(item, source)
        await session.commit()

        page_again = await connector.search(ConnectorSearchFilter(brand="Seat", page_size=100))
        outcomes = [await service.ingest_raw(item, source) for item in page_again.items]
        await session.commit()

        assert await _count(session, VehicleListing) == page.total
        assert await _count(session, RawListingPayload) == page.total
        assert all(o.created is False and o.updated is False for o in outcomes)


async def test_price_change_creates_new_snapshot(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    connector = MockConnector(latency_enabled=False, faults_enabled=False)
    page = await connector.search(ConnectorSearchFilter(brand="Dacia", page_size=10))
    original = page.items[0]

    async with session_factory() as session:
        source = await _mock_source(session)
        service = ListingService(session)
        first = await service.ingest_raw(original, source)
        await session.commit()

        cheaper_payload = dict(original.payload)
        cheaper_payload["precio"] = int(cheaper_payload["precio"]) - 500
        cheaper = original.model_copy(update={"payload": cheaper_payload})
        second = await service.ingest_raw(cheaper, source)
        await session.commit()

        assert second.updated is True
        assert second.snapshot_created is True
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
