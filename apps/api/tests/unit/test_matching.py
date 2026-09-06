from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from app.listings.vocab import FuelType, Transmission
from app.vehicles.matching import MatchResult, score_match


def _dummy_listing(
    *,
    brand: str = "SEAT",
    model: str = "Ibiza",
    year: int = 2015,
    mileage_km: int = 120000,
    price_amount: Decimal = Decimal("4500.00"),
    fuel_type: FuelType = FuelType.DIESEL,
    transmission: Transmission = Transmission.MANUAL,
    province: str | None = "Madrid",
    trim: str | None = "1.6 TDI Style",
    description: str | None = "Coche en perfecto estado, único dueño, mantenimientos al día.",
) -> dict:
    return {
        "id": uuid4(),
        "brand": brand,
        "model": model,
        "year": year,
        "mileage_km": mileage_km,
        "price_amount": price_amount,
        "fuel_type": fuel_type,
        "transmission": transmission,
        "province": province,
        "trim": trim,
        "description": description,
    }


@pytest.mark.unit
def test_matching_identical_listings_gives_high_confidence() -> None:
    l1 = _dummy_listing()
    l2 = _dummy_listing(price_amount=Decimal("4400.00"), mileage_km=121000)
    result = score_match(l1, l2)
    assert isinstance(result, MatchResult)
    assert result.confidence >= Decimal("0.85")
    assert "brand" in result.reasons
    assert "model" in result.reasons
    assert "year" in result.reasons
    assert "fuel_type" in result.reasons
    assert "mileage" in result.reasons


@pytest.mark.unit
def test_matching_different_brands_gives_zero_confidence() -> None:
    l1 = _dummy_listing(brand="SEAT")
    l2 = _dummy_listing(brand="Volkswagen")
    result = score_match(l1, l2)
    assert result.confidence == Decimal("0.000")
    assert result.reasons.get("brand_mismatch") is True


@pytest.mark.unit
def test_matching_different_fuel_types_gives_zero_confidence() -> None:
    l1 = _dummy_listing(fuel_type=FuelType.DIESEL)
    l2 = _dummy_listing(fuel_type=FuelType.PETROL)
    result = score_match(l1, l2)
    assert result.confidence == Decimal("0.000")
    assert result.reasons.get("fuel_type_mismatch") is True


@pytest.mark.unit
def test_matching_different_transmission_gives_zero_confidence() -> None:
    l1 = _dummy_listing(transmission=Transmission.MANUAL)
    l2 = _dummy_listing(transmission=Transmission.AUTOMATIC)
    result = score_match(l1, l2)
    assert result.confidence == Decimal("0.000")
    assert result.reasons.get("transmission_mismatch") is True


@pytest.mark.unit
def test_matching_year_difference_penalization() -> None:
    l1 = _dummy_listing(year=2015)
    l2_same = _dummy_listing(year=2015)
    l2_one_year = _dummy_listing(year=2016)
    l2_two_years = _dummy_listing(year=2017)

    res_same = score_match(l1, l2_same)
    res_one = score_match(l1, l2_one_year)
    res_two = score_match(l1, l2_two_years)

    assert res_same.confidence > res_one.confidence
    assert res_one.confidence > res_two.confidence
    assert res_two.reasons["year_score"] == 0.0


@pytest.mark.unit
def test_matching_mileage_and_price_tolerance() -> None:
    l1 = _dummy_listing(mileage_km=100000, price_amount=Decimal("5000.00"))
    l2_close = _dummy_listing(mileage_km=102000, price_amount=Decimal("5100.00"))
    l2_far = _dummy_listing(mileage_km=180000, price_amount=Decimal("9000.00"))

    res_close = score_match(l1, l2_close)
    res_far = score_match(l1, l2_far)

    assert res_close.confidence > res_far.confidence
    assert res_far.confidence < Decimal("0.60")


@pytest.mark.unit
def test_matching_is_symmetric() -> None:
    l1 = _dummy_listing(mileage_km=100000, province="Barcelona")
    l2 = _dummy_listing(mileage_km=104000, province="Madrid")

    res1 = score_match(l1, l2)
    res2 = score_match(l2, l1)

    assert res1.confidence == res2.confidence
    assert res1.reasons == res2.reasons


@pytest.mark.unit
def test_matching_with_none_fields_handled_gracefully() -> None:
    l1 = _dummy_listing(province=None, trim=None, description=None)
    l2 = _dummy_listing(province=None, trim=None, description=None)

    result = score_match(l1, l2)
    assert result.confidence > Decimal("0.70")


@pytest.mark.unit
def test_matching_unknown_transmission_is_allowed() -> None:
    l1 = _dummy_listing(transmission=Transmission.UNKNOWN)
    l2 = _dummy_listing(transmission=Transmission.MANUAL)
    result = score_match(l1, l2)
    assert result.confidence > Decimal("0.70")


@pytest.mark.unit
def test_matching_zero_mileage_and_price_handled() -> None:
    l1 = _dummy_listing(mileage_km=0, price_amount=Decimal("0.00"))
    l2 = _dummy_listing(mileage_km=0, price_amount=Decimal("0.00"))
    result = score_match(l1, l2)
    assert result.confidence >= Decimal("0.85")


@pytest.mark.unit
def test_matching_empty_brand_gives_zero() -> None:
    l1 = _dummy_listing(brand="")
    l2 = _dummy_listing(brand="SEAT")
    result = score_match(l1, l2)
    assert result.confidence == Decimal("0.000")
    assert result.reasons.get("brand_mismatch") is True
