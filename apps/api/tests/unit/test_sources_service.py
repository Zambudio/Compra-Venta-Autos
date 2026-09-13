from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import app.models  # noqa: F401
import pytest
from app.connectors.errors import TransientConnectorError, UnknownConnectorError
from app.connectors.filters import ConnectorSearchFilter
from app.connectors.schemas import ConnectorSearchPage
from app.listings.vocab import ProviderKind, SyncRunStatus
from app.sources.models import Source, SourceConfig, SourceConfigChange, SourceSyncRun
from app.sources.service import (
    LastActiveSourceError,
    SourceService,
    _apply_sync_status,
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

    health = await service.health("manual")

    assert health.source_key == "manual"
    assert health.healthy is True


@pytest.mark.asyncio
async def test_health_rejects_unknown_source() -> None:
    service = SourceService(AsyncMock(spec=AsyncSession))

    with pytest.raises(UnknownConnectorError):
        await service.health("unsupported")


@pytest.mark.asyncio
async def test_update_source_config_persists_change_and_audit_actor() -> None:
    db = AsyncMock(spec=AsyncSession)
    manual = Source(
        id=uuid4(),
        key="manual",
        name="Entrada manual",
        provider_kind=ProviderKind.MANUAL,
        is_active=True,
    )
    wallapop = Source(
        id=uuid4(),
        key="wallapop",
        name="Wallapop",
        provider_kind=ProviderKind.CONNECTOR,
        is_active=True,
    )
    configuration = SourceConfig(
        id=uuid4(),
        source_key="wallapop",
        enabled=True,
        config={"timeout": 10},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    sources_result = MagicMock()
    sources_result.scalars.return_value.all.return_value = [manual, wallapop]
    config_result = MagicMock()
    config_result.scalar_one_or_none.return_value = configuration
    db.execute.side_effect = [sources_result, config_result]
    actor_id = uuid4()

    updated = await SourceService(db).update_source_config(
        "wallapop", enabled=False, config={"timeout": 15}, changed_by=actor_id
    )

    assert updated.enabled is False
    assert updated.config == {"timeout": 15}
    assert wallapop.is_active is False
    audit = next(
        call.args[0]
        for call in db.add.call_args_list
        if isinstance(call.args[0], SourceConfigChange)
    )
    assert audit.before == {"enabled": True, "config": {"timeout": 10}}
    assert audit.after == {"enabled": False, "config": {"timeout": 15}}
    assert audit.changed_by == actor_id


@pytest.mark.asyncio
async def test_update_source_config_refuses_to_disable_last_active_connector() -> None:
    db = AsyncMock(spec=AsyncSession)
    wallapop = Source(
        id=uuid4(),
        key="wallapop",
        name="Wallapop",
        provider_kind=ProviderKind.CONNECTOR,
        is_active=True,
    )
    result = MagicMock()
    result.scalars.return_value.all.return_value = [wallapop]
    db.execute.return_value = result

    with pytest.raises(LastActiveSourceError):
        await SourceService(db).update_source_config(
            "wallapop", enabled=False, config=None, changed_by=uuid4()
        )

    db.add.assert_not_called()


def test_sync_status_updates_configuration_observability() -> None:
    finished_at = datetime.now(UTC)
    configuration = SourceConfig(source_key="wallapop", enabled=True, config={})
    run = SourceSyncRun(
        source_id=uuid4(),
        status=SyncRunStatus.PARTIAL,
        mode="sync",
        filters={},
        error_summary="upstream unavailable",
        finished_at=finished_at,
    )

    _apply_sync_status(configuration, run)

    assert configuration.last_sync == finished_at
    assert configuration.sync_error == "upstream unavailable"


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
