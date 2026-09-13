from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.connectors.errors import ConnectorRateLimitError
from app.connectors.filters import ConnectorSearchFilter
from app.connectors.schemas import ConnectorSearchPage, RawListing
from app.listings.schemas import LiveSearchFilters
from app.listings.service import (
    ListingService,
    LiveSearchRateLimitError,
    LiveSourceDisabledError,
)
from app.sources.models import SourceConfig
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.unit


class MemoryRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.counters: dict[str, int] = {}

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def setex(self, key: str, _ttl: int, value: str) -> None:
        self.values[key] = value

    async def eval(self, _script: str, _keys: int, key: str, _window: int) -> int:
        self.counters[key] = self.counters.get(key, 0) + 1
        return self.counters[key]


class RecordingConnector:
    def __init__(self) -> None:
        self.calls: list[ConnectorSearchFilter] = []

    async def search(self, filters: ConnectorSearchFilter) -> ConnectorSearchPage:
        self.calls.append(filters)
        raw = RawListing(
            source_key="wallapop",
            external_id="w-123",
            url="https://es.wallapop.com/item/seat-ibiza-w-123",
            retrieved_at=datetime(2026, 9, 13, tzinfo=UTC),
            connector_version="wallapop-api-v3",
            payload={
                "id": "w-123",
                "title": "SEAT Ibiza 1.6 TDI",
                "description": "Vehículo cuidado",
                "price": 5900,
                "location": {"city": "Madrid"},
                "images": [{"original": "https://img.example/w-123.jpg"}],
                "user": {
                    "micro_name": "Motor Madrid",
                    "scoring_stars": 4.8,
                    "web_slug": "motor-madrid",
                },
                "publish_date": "2026-09-12T10:30:00Z",
            },
        )
        return ConnectorSearchPage(items=[raw], page=1, page_size=20, total=1, has_more=False)


def _db_with_configuration(enabled: bool = True) -> tuple[AsyncMock, SourceConfig]:
    db = AsyncMock(spec=AsyncSession)
    configuration = SourceConfig(
        id=uuid4(),
        source_key="wallapop",
        enabled=enabled,
        config={"rate_limit_per_hour": 100},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    result = MagicMock()
    result.scalar_one_or_none.return_value = configuration
    db.execute.return_value = result
    return db, configuration


@pytest.mark.asyncio
async def test_live_search_normalizes_wallapop_result_and_caches_identical_query() -> None:
    db, configuration = _db_with_configuration()
    cache = MemoryRedis()
    connector = RecordingConnector()
    filters = LiveSearchFilters(
        query="SEAT Ibiza", min_price=3000, max_price=7000, location="Madrid"
    )
    service = ListingService(db)

    first = await service.search_live(filters, cache=cache, connector=connector)
    second = await service.search_live(filters, cache=cache, connector=connector)

    assert first == second
    assert len(connector.calls) == 1
    assert connector.calls[0].query == "SEAT Ibiza"
    assert connector.calls[0].price_min == 3000
    assert first.total == 1
    assert first.listings[0].id == "w-123"
    assert first.listings[0].price == 5900
    assert first.listings[0].seller == {
        "name": "Motor Madrid",
        "rating": 4.8,
        "url": "motor-madrid",
    }
    assert configuration.last_sync is not None
    assert configuration.sync_error is None


@pytest.mark.asyncio
async def test_live_search_rejects_disabled_wallapop_before_cache_or_network() -> None:
    db, _configuration = _db_with_configuration(enabled=False)
    cache = MemoryRedis()
    connector = RecordingConnector()

    with pytest.raises(LiveSourceDisabledError):
        await ListingService(db).search_live(
            LiveSearchFilters(query="BMW 320"), cache=cache, connector=connector
        )

    assert connector.calls == []
    assert cache.values == {}


@pytest.mark.asyncio
async def test_live_search_limits_outbound_calls_per_source_configuration() -> None:
    db, configuration = _db_with_configuration()
    configuration.config = {"rate_limit_per_hour": 1}
    cache = MemoryRedis()
    connector = RecordingConnector()
    service = ListingService(db)

    await service.search_live(LiveSearchFilters(query="BMW 320"), cache=cache, connector=connector)
    with pytest.raises(LiveSearchRateLimitError):
        await service.search_live(
            LiveSearchFilters(query="Audi A4"), cache=cache, connector=connector
        )

    assert len(connector.calls) == 1


@pytest.mark.asyncio
async def test_live_search_maps_wallapop_429_and_records_sync_error() -> None:
    db, configuration = _db_with_configuration()
    cache = MemoryRedis()
    connector = RecordingConnector()

    async def rate_limited(_filters: ConnectorSearchFilter) -> ConnectorSearchPage:
        raise ConnectorRateLimitError("Wallapop devolvió 429", retry_after_seconds=90)

    connector.search = rate_limited  # type: ignore[method-assign]

    with pytest.raises(LiveSearchRateLimitError) as exc_info:
        await ListingService(db).search_live(
            LiveSearchFilters(query="BMW 320"), cache=cache, connector=connector
        )

    assert exc_info.value.retry_after_seconds == 90
    assert configuration.sync_error == "Wallapop devolvió 429"
