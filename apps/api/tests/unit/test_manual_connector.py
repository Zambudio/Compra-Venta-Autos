from __future__ import annotations

import pytest
from app.connectors.filters import ConnectorSearchFilter
from app.connectors.manual import ManualEntryConnector

pytestmark = pytest.mark.unit


async def test_manual_search_returns_empty_page() -> None:
    page = await ManualEntryConnector().search(ConnectorSearchFilter())

    assert page.items == []
    assert page.total == 0
    assert page.has_more is False


async def test_manual_fetch_returns_none() -> None:
    assert (await ManualEntryConnector().fetch("manual-anything")) is None


async def test_manual_health_check_is_healthy() -> None:
    health = await ManualEntryConnector().health_check()

    assert health.source_key == "manual"
    assert health.healthy is True


def test_build_raw_wraps_submission_payload() -> None:
    submission = {
        "external_id": "manual-abc123",
        "url": "https://example.com/anuncio",
        "marca": "Seat",
        "modelo": "Ibiza",
        "anio": 2014,
        "km": 120000,
        "precio": 4200,
    }

    raw = ManualEntryConnector().build_raw(submission)

    assert raw.source_key == "manual"
    assert raw.external_id == "manual-abc123"
    assert raw.url == "https://example.com/anuncio"
    assert raw.payload["marca"] == "Seat"
    assert raw.connector_version


def test_build_raw_requires_external_id() -> None:
    with pytest.raises(KeyError):
        ManualEntryConnector().build_raw({"marca": "Seat"})
