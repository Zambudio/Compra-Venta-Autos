from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from app.connectors.errors import TransientConnectorError, UnknownConnectorError
from app.connectors.filters import ConnectorSearchFilter
from app.connectors.schemas import ConnectorSearchPage
from app.listings.vocab import SyncRunStatus
from app.sources.service import (
    SourceService,
    _connector_filter,
    _final_status,
    _sanitize,
    _search_with_retry,
)
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("errors", "seen", "changed", "expected"),
    [
        ([], 10, 5, SyncRunStatus.SUCCESS),
        (["page 4: down"], 8, 3, SyncRunStatus.PARTIAL),
        (["page 1: down"], 0, 0, SyncRunStatus.FAILED),
    ],
)
def test_final_status(errors: list[str], seen: int, changed: int, expected: SyncRunStatus) -> None:
    assert _final_status(errors=errors, seen=seen, changed=changed) is expected


def test_sanitize_is_none_for_empty_and_truncates() -> None:
    assert _sanitize([]) is None
    long = _sanitize(["x" * 400, "y" * 400])
    assert long is not None
    assert len(long) == 500


def test_connector_filter_rebuilds_from_stored_dict() -> None:
    connector_filter = _connector_filter(
        {"brand": "Seat", "price_max": "5000", "fuel_type": "DIESEL"}, page=2, page_size=30
    )

    assert connector_filter.brand == "Seat"
    assert connector_filter.page == 2
    assert connector_filter.page_size == 30


@pytest.mark.asyncio
async def test_health_uses_connector_registry() -> None:
    service = SourceService(AsyncMock(spec=AsyncSession))

    health = await service.health("mock")

    assert health.source_key == "mock"
    assert health.healthy is True


@pytest.mark.asyncio
async def test_health_rejects_unknown_source() -> None:
    service = SourceService(AsyncMock(spec=AsyncSession))

    with pytest.raises(UnknownConnectorError):
        await service.health("wallapop")


class _FlakyConnector:
    def __init__(self, failures: int) -> None:
        self.calls = 0
        self._failures = failures

    async def search(self, connector_filter: ConnectorSearchFilter) -> ConnectorSearchPage:
        self.calls += 1
        if self.calls <= self._failures:
            raise TransientConnectorError("temporary")
        return ConnectorSearchPage(items=[], page=1, page_size=20, total=0, has_more=False)


@pytest.mark.asyncio
async def test_search_with_retry_recovers_after_transient_failures() -> None:
    connector = _FlakyConnector(failures=2)

    page = await _search_with_retry(connector, ConnectorSearchFilter())  # type: ignore[arg-type]

    assert page.total == 0
    assert connector.calls == 3


@pytest.mark.asyncio
async def test_search_with_retry_gives_up_after_max_attempts() -> None:
    connector = _FlakyConnector(failures=99)

    with pytest.raises(TransientConnectorError):
        await _search_with_retry(connector, ConnectorSearchFilter())  # type: ignore[arg-type]

    assert connector.calls == 3
