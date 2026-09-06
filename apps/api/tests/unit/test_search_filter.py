from __future__ import annotations

from decimal import Decimal

import pytest
from app.listings.vocab import FuelType, SellerType
from app.search.schemas import SearchFilter, SortOrder
from pydantic import ValidationError

pytestmark = pytest.mark.unit


def test_defaults_are_sensible() -> None:
    f = SearchFilter()

    assert f.page == 1
    assert f.page_size == 20
    assert f.sort is SortOrder.NEWEST
    assert f.source == []


def test_parses_typed_values() -> None:
    f = SearchFilter.model_validate(
        {
            "brand": "Seat",
            "fuel_type": "DIESEL",
            "seller_type": "PRIVATE",
            "price_max": "5000",
            "sort": "price_asc",
            "page_size": 50,
        }
    )

    assert f.fuel_type is FuelType.DIESEL
    assert f.seller_type is SellerType.PRIVATE
    assert f.price_max == Decimal("5000")
    assert f.sort is SortOrder.PRICE_ASC


def test_rejects_inverted_year_range() -> None:
    with pytest.raises(ValidationError):
        SearchFilter(year_min=2018, year_max=2015)


def test_rejects_inverted_price_range() -> None:
    with pytest.raises(ValidationError):
        SearchFilter(price_min=Decimal("9000"), price_max=Decimal("2000"))


def test_rejects_oversized_page() -> None:
    with pytest.raises(ValidationError):
        SearchFilter(page_size=500)


def test_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        SearchFilter.model_validate({"colour": "red"})


def test_to_connector_filter_overrides_pagination() -> None:
    f = SearchFilter(brand="Ford", price_max=Decimal("6000"), page=3, page_size=20)

    connector_filter = f.to_connector_filter(page=2, page_size=50)

    assert connector_filter.brand == "Ford"
    assert connector_filter.price_max == Decimal("6000")
    assert connector_filter.page == 2
    assert connector_filter.page_size == 50
