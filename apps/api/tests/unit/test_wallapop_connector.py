from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.connectors.errors import TransientConnectorError
from app.connectors.filters import ConnectorSearchFilter
from app.connectors.wallapop import WallapopConnector

pytestmark = pytest.mark.unit


@pytest.fixture
def connector():
    return WallapopConnector()


def test_search_builds_correct_params(connector: WallapopConnector) -> None:
    """Test that search builds correct query parameters for Wallapop API."""
    filters = ConnectorSearchFilter(
        page=2,
        page_size=20,
        brand="SEAT",
        year_min=2010,
        year_max=2020,
        price_min=2000,
        price_max=5000,
    )
    params = connector._build_params(filters)

    assert params["start"] == 20  # (page-1)*page_size
    assert params["step"] == 20
    assert params["brand"] == "SEAT"
    assert params["min_year"] == 2010
    assert params["max_year"] == 2020
    assert params["min_sale_price"] == 2000
    assert params["max_sale_price"] == 5000


def test_search_returns_normalized_listings(connector: WallapopConnector) -> None:
    """Test that _to_raw normalizes API responses into RawListing objects."""
    item = {
        "id": "item-1",
        "web_slug": "https://wallapop.com/item/item-1",
        "title": "SEAT Ibiza 2014",
        "price": 2800,
        "brand": "SEAT",
        "model": "Ibiza",
    }

    result = connector._to_raw(item)

    assert result.external_id == "item-1"
    assert result.source_key == "wallapop"
    assert result.url == "https://wallapop.com/item/item-1"


@pytest.mark.asyncio
async def test_search_handles_403_blocking(connector: WallapopConnector) -> None:
    """Test that 403 errors are reported as transient connector errors."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get.return_value.status_code = 403

        filters = ConnectorSearchFilter()
        with pytest.raises(TransientConnectorError, match="403"):
            await connector.search(filters)


@pytest.mark.asyncio
async def test_search_handles_429_rate_limit(connector: WallapopConnector) -> None:
    """Test that 429 rate limit errors are reported as transient connector errors."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get.return_value.status_code = 429

        filters = ConnectorSearchFilter()
        with pytest.raises(TransientConnectorError, match="429"):
            await connector.search(filters)


@pytest.mark.asyncio
async def test_search_handles_5xx_errors(connector: WallapopConnector) -> None:
    """Test that 5xx server errors are reported as transient connector errors."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get.return_value.status_code = 503

        filters = ConnectorSearchFilter()
        with pytest.raises(TransientConnectorError, match="503"):
            await connector.search(filters)


@pytest.mark.asyncio
async def test_search_handles_timeout(connector: WallapopConnector) -> None:
    """Test that timeout errors are handled gracefully."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get.side_effect = httpx.TimeoutException("timeout")

        filters = ConnectorSearchFilter()
        with pytest.raises(TransientConnectorError, match="Timeout"):
            await connector.search(filters)


@pytest.mark.asyncio
async def test_fetch_returns_none_for_404(connector: WallapopConnector) -> None:
    """Test that fetch returns None for 404 responses."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get.return_value.status_code = 404

        result = await connector.fetch("missing-item")

        assert result is None


def test_fetch_returns_raw_listing(connector: WallapopConnector) -> None:
    """Test that _to_raw normalizes fetch responses."""
    item_data = {
        "id": "item-123",
        "web_slug": "https://wallapop.com/item/item-123",
        "title": "SEAT Ibiza",
    }

    result = connector._to_raw(item_data)

    assert result is not None
    assert result.external_id == "item-123"
    assert result.source_key == "wallapop"
    assert result.url == "https://wallapop.com/item/item-123"


@pytest.mark.asyncio
async def test_health_check_when_api_accessible(connector: WallapopConnector) -> None:
    """Test health check when API is accessible."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get.return_value.status_code = 200

        health = await connector.health_check()

        assert health.source_key == "wallapop"
        assert health.healthy is True
        assert "accesible" in health.detail.lower()


@pytest.mark.asyncio
async def test_health_check_when_blocked_403(connector: WallapopConnector) -> None:
    """Test health check when API returns 403."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get.return_value.status_code = 403

        health = await connector.health_check()

        assert health.healthy is False
        assert "403" in health.detail


@pytest.mark.asyncio
async def test_health_check_when_rate_limited_429(connector: WallapopConnector) -> None:
    """Test health check when API returns 429."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get.return_value.status_code = 429

        health = await connector.health_check()

        assert health.healthy is False
        assert "429" in health.detail


@pytest.mark.asyncio
async def test_health_check_when_timeout(connector: WallapopConnector) -> None:
    """Test health check when connection times out."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get.side_effect = httpx.TimeoutException("timeout")

        health = await connector.health_check()

        assert health.healthy is False
        assert "Timeout" in health.detail


@pytest.mark.asyncio
async def test_health_check_includes_timestamp(connector: WallapopConnector) -> None:
    """Test that health check includes a checked_at timestamp."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get.return_value.status_code = 200

        before = datetime.now(UTC)
        health = await connector.health_check()
        after = datetime.now(UTC)

        assert before <= health.checked_at <= after


@pytest.mark.asyncio
async def test_to_raw_handles_missing_fields(connector: WallapopConnector) -> None:
    """Test that _to_raw normalizes items with missing fields."""
    item = {"item_id": "123"}  # Minimal item

    raw = connector._to_raw(item)

    assert raw.external_id == "123"
    assert raw.url == ""
    assert raw.source_key == "wallapop"
