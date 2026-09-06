from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.listings.vocab import ListingStatus
from app.vehicles.history import calculate_listing_history, calculate_vehicle_history
from app.vehicles.market import MarketEstimateResult, estimate_market_price


class _DummySnapshot:
    def __init__(
        self, price: str, observed_at: datetime, status: ListingStatus = ListingStatus.ACTIVE
    ) -> None:
        self.price_amount = Decimal(price)
        self.observed_at = observed_at
        self.status = status


@pytest.mark.unit
def test_calculate_listing_history_with_single_snapshot() -> None:
    now = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
    snaps = [_DummySnapshot("5000.00", now)]
    h = calculate_listing_history(snaps)
    assert h.initial_price == Decimal("5000.00")
    assert h.current_price == Decimal("5000.00")
    assert h.price_delta == Decimal("0.00")
    assert h.price_delta_percentage == Decimal("0.00")
    assert h.days_on_market == 0
    assert h.number_of_price_changes == 0
    assert h.is_relisted is False


@pytest.mark.unit
def test_calculate_listing_history_price_drop_and_relist() -> None:
    t0 = datetime(2026, 8, 1, 10, 0, tzinfo=UTC)
    t1 = t0 + timedelta(days=10)
    t2 = t0 + timedelta(days=20)
    t3 = t0 + timedelta(days=30)

    snaps = [
        _DummySnapshot("6000.00", t0, ListingStatus.ACTIVE),
        _DummySnapshot("5500.00", t1, ListingStatus.ACTIVE),
        _DummySnapshot("5500.00", t2, ListingStatus.WITHDRAWN),
        _DummySnapshot("5200.00", t3, ListingStatus.ACTIVE),
    ]
    h = calculate_listing_history(snaps)
    assert h.initial_price == Decimal("6000.00")
    assert h.current_price == Decimal("5200.00")
    assert h.price_delta == Decimal("-800.00")
    assert h.price_delta_percentage == Decimal("-13.33")
    assert h.days_on_market == 30
    assert h.number_of_price_changes == 2
    assert h.is_relisted is True


@pytest.mark.unit
def test_calculate_listing_history_empty_snapshots() -> None:
    h = calculate_listing_history([])
    assert h.initial_price == Decimal("0.00")
    assert h.days_on_market == 0


@pytest.mark.unit
def test_calculate_vehicle_history_multiple_listings() -> None:
    t0 = datetime(2026, 8, 1, 10, 0, tzinfo=UTC)
    t1 = t0 + timedelta(days=15)

    l1_snaps = [
        _DummySnapshot("5000.00", t0),
        _DummySnapshot("4800.00", t1),
    ]
    l2_snaps = [
        _DummySnapshot("4900.00", t0 + timedelta(days=5)),
    ]

    h = calculate_vehicle_history(
        [l1_snaps, l2_snaps], current_prices=[Decimal("4800.00"), Decimal("4900.00")]
    )
    assert h.lowest_observed_price == Decimal("4800.00")
    assert h.highest_observed_price == Decimal("5000.00")
    assert h.current_min_price == Decimal("4800.00")
    assert h.days_on_market == 15
    assert h.total_price_changes == 1


@pytest.mark.unit
def test_estimate_market_price_without_comparables() -> None:
    subject = {
        "brand": "SEAT",
        "model": "Ibiza",
        "year": 2015,
        "mileage_km": 120000,
        "price_amount": Decimal("5000.00"),
        "fuel_type": "DIESEL",
    }
    est = estimate_market_price(subject, [])
    assert isinstance(est, MarketEstimateResult)
    assert est.number_of_comparables == 0
    assert est.confidence_score <= Decimal("0.300")
    assert est.estimated_amount == Decimal("5000.00")


@pytest.mark.unit
def test_estimate_market_price_with_comparables_and_outlier_filtering() -> None:
    subject = {
        "brand": "SEAT",
        "model": "Ibiza",
        "year": 2015,
        "mileage_km": 120000,
        "price_amount": Decimal("4800.00"),
        "fuel_type": "DIESEL",
    }
    # Pool de comparables homogéneos + 1 outlier extremo
    pool = [
        {
            "brand": "SEAT",
            "model": "Ibiza",
            "year": 2015,
            "mileage_km": 122000,
            "price_amount": Decimal("4600.00"),
            "fuel_type": "DIESEL",
        },
        {
            "brand": "SEAT",
            "model": "Ibiza",
            "year": 2016,
            "mileage_km": 118000,
            "price_amount": Decimal("4800.00"),
            "fuel_type": "DIESEL",
        },
        {
            "brand": "SEAT",
            "model": "Ibiza",
            "year": 2014,
            "mileage_km": 125000,
            "price_amount": Decimal("4500.00"),
            "fuel_type": "DIESEL",
        },
        {
            "brand": "SEAT",
            "model": "Ibiza",
            "year": 2015,
            "mileage_km": 120000,
            "price_amount": Decimal("5000.00"),
            "fuel_type": "DIESEL",
        },
        {
            "brand": "SEAT",
            "model": "Ibiza",
            "year": 2015,
            "mileage_km": 115000,
            "price_amount": Decimal("4700.00"),
            "fuel_type": "DIESEL",
        },
        # Outlier extremo que debe ser filtrado por IQR
        {
            "brand": "SEAT",
            "model": "Ibiza",
            "year": 2015,
            "mileage_km": 120000,
            "price_amount": Decimal("15000.00"),
            "fuel_type": "DIESEL",
        },
        # Incompatible que debe ser descartado (gasolina)
        {
            "brand": "SEAT",
            "model": "Ibiza",
            "year": 2015,
            "mileage_km": 120000,
            "price_amount": Decimal("4900.00"),
            "fuel_type": "PETROL",
        },
    ]

    est = estimate_market_price(subject, pool)
    assert est.number_of_comparables == 5
    assert Decimal("4600.00") <= est.estimated_amount <= Decimal("4900.00")
    assert est.low_amount < est.estimated_amount
    assert est.high_amount > est.estimated_amount
    assert est.confidence_score > Decimal("0.300")
