from __future__ import annotations

from decimal import Decimal

import pytest
from app.connectors.errors import TransientConnectorError
from app.connectors.filters import ConnectorSearchFilter
from app.connectors.mock.connector import MockConnector
from app.listings.vocab import FuelType, SellerType

pytestmark = pytest.mark.unit


def _connector() -> MockConnector:
    return MockConnector(latency_enabled=False, faults_enabled=False)


async def test_search_is_deterministic() -> None:
    connector = _connector()
    first = await connector.search(ConnectorSearchFilter(page_size=50))
    second = await connector.search(ConnectorSearchFilter(page_size=50))

    assert [item.external_id for item in first.items] == [item.external_id for item in second.items]
    assert first.total == second.total


async def test_search_returns_raw_listings_with_payload() -> None:
    page = await _connector().search(ConnectorSearchFilter(page_size=1))

    item = page.items[0]
    assert item.source_key == "mock"
    assert item.external_id.startswith("mock-")
    assert item.payload["marca"]
    assert item.connector_version


async def test_filter_by_brand_is_case_insensitive() -> None:
    page = await _connector().search(ConnectorSearchFilter(brand="seat", page_size=50))

    assert page.items
    assert all(item.payload["marca"].lower() == "seat" for item in page.items)


async def test_filter_by_price_range() -> None:
    page = await _connector().search(
        ConnectorSearchFilter(price_min=Decimal("3000"), price_max=Decimal("5000"), page_size=50)
    )

    assert page.items
    assert all(3000 <= item.payload["precio"] <= 5000 for item in page.items)


async def test_filter_by_year_range() -> None:
    page = await _connector().search(
        ConnectorSearchFilter(year_min=2015, year_max=2016, page_size=50)
    )

    assert page.items
    assert all(2015 <= item.payload["anio"] <= 2016 for item in page.items)


async def test_filter_by_year_max_excludes_newer() -> None:
    page = await _connector().search(ConnectorSearchFilter(year_max=2010, page_size=50))

    assert page.items
    assert all(item.payload["anio"] <= 2010 for item in page.items)


async def test_filter_by_model_substring() -> None:
    page = await _connector().search(ConnectorSearchFilter(model="corsa", page_size=50))

    assert page.items
    assert all("corsa" in item.payload["modelo"].lower() for item in page.items)


async def test_latency_enabled_still_returns_results() -> None:
    page = await MockConnector(latency_enabled=True, faults_enabled=False).search(
        ConnectorSearchFilter(brand="Seat", page_size=5)
    )

    assert page.items


async def test_filter_by_fuel_type() -> None:
    page = await _connector().search(ConnectorSearchFilter(fuel_type=FuelType.PETROL, page_size=50))

    assert page.items
    assert all(item.payload["combustible"].lower() in {"gasolina", "petrol"} for item in page.items)


async def test_filter_by_mileage_max() -> None:
    page = await _connector().search(ConnectorSearchFilter(mileage_max=100000, page_size=50))

    assert page.items
    assert all(item.payload["km"] <= 100000 for item in page.items)


async def test_filter_by_province() -> None:
    page = await _connector().search(ConnectorSearchFilter(province="Madrid", page_size=50))

    assert page.items
    assert all(item.payload["provincia"] == "Madrid" for item in page.items)


async def test_filter_by_seller_type() -> None:
    page = await _connector().search(
        ConnectorSearchFilter(seller_type=SellerType.DEALER, page_size=50)
    )

    assert page.items
    assert all(item.payload["vendedor"] == "profesional" for item in page.items)


async def test_pagination_splits_results_without_overlap() -> None:
    connector = _connector()
    page_one = await connector.search(ConnectorSearchFilter(page=1, page_size=20))
    page_two = await connector.search(ConnectorSearchFilter(page=2, page_size=20))

    assert len(page_one.items) == 20
    assert page_one.has_more is True
    assert page_two.has_more is False
    assert page_one.total == page_two.total >= 21
    ids_one = {item.external_id for item in page_one.items}
    ids_two = {item.external_id for item in page_two.items}
    assert ids_one.isdisjoint(ids_two)


async def test_empty_filter_result_has_no_items() -> None:
    page = await _connector().search(ConnectorSearchFilter(brand="Ferrari", page_size=50))

    assert page.items == []
    assert page.total == 0
    assert page.has_more is False


async def test_fetch_returns_single_listing_or_none() -> None:
    connector = _connector()
    assert (await connector.fetch("mock-0001")) is not None
    assert (await connector.fetch("mock-9999")) is None


async def test_health_check_reports_healthy() -> None:
    health = await _connector().health_check()

    assert health.source_key == "mock"
    assert health.healthy is True


async def test_transient_faults_are_deterministic() -> None:
    faulty = MockConnector(latency_enabled=False, faults_enabled=True)

    with pytest.raises(TransientConnectorError):
        await faulty.search(ConnectorSearchFilter(page=4, page_size=5))

    # Same call fails the same way; a page without a fault succeeds.
    with pytest.raises(TransientConnectorError):
        await faulty.search(ConnectorSearchFilter(page=4, page_size=5))
    assert (await faulty.search(ConnectorSearchFilter(page=1, page_size=5))).items


async def test_faults_disabled_never_raises() -> None:
    connector = MockConnector(latency_enabled=False, faults_enabled=False)
    for page in range(1, 9):
        await connector.search(ConnectorSearchFilter(page=page, page_size=5))
