"""Tests unitarios para la valoración económica, intervalos y presión del vendedor (Fase 5)."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.scoring.valuation import compute_economic_valuation, compute_seller_pressure
from app.scoring.vocab import ConfidenceLevel, SellerPressureLevel


@pytest.mark.unit
def test_seller_pressure_levels_and_reasons() -> None:
    now = datetime.now(UTC)

    # 1. Anuncio recién publicado sin rebajas (LOW)
    level_low, reasons_low, days_l, red_cnt_l, red_amt_l, red_pct_l = compute_seller_pressure(
        published_at=now - timedelta(days=2),
        last_seen_at=now,
        snapshots=[],
        current_price=Decimal("2500.00"),
    )
    assert level_low == SellerPressureLevel.LOW
    assert days_l == 2
    assert red_cnt_l == 0
    assert red_amt_l == Decimal("0.00")
    assert any("Baja presión" in r for r in reasons_low)

    # 2. Anuncio con 50 días y 2 rebajas acumulando 20% (HIGH)
    snap1 = MagicMock(
        observed_at=now - timedelta(days=50),
        snapshot_at=now - timedelta(days=50),
        price_amount=Decimal("3000.00"),
    )
    snap2 = MagicMock(
        observed_at=now - timedelta(days=25),
        snapshot_at=now - timedelta(days=25),
        price_amount=Decimal("2700.00"),
    )
    level_high, reasons_high, days_h, red_cnt_h, red_amt_h, red_pct_h = compute_seller_pressure(
        published_at=now - timedelta(days=50),
        last_seen_at=now,
        snapshots=[snap1, snap2],
        current_price=Decimal("2400.00"),
    )
    assert level_high == SellerPressureLevel.HIGH
    assert days_h == 50
    assert red_cnt_h == 2
    assert red_amt_h == Decimal("600.00")
    assert red_pct_h == Decimal("20.00")
    assert any("Alta presión" in r for r in reasons_high)

    # 3. Anuncio moderado (MEDIUM): 28 días publicado
    level_med, _, days_m, _, _, _ = compute_seller_pressure(
        published_at=now - timedelta(days=28),
        last_seen_at=now,
        snapshots=[],
        current_price=Decimal("2000.00"),
    )
    assert level_med == SellerPressureLevel.MEDIUM
    assert days_m == 28


@pytest.mark.unit
def test_economic_valuation_breakdown_and_itp() -> None:
    # Caso con estimación de mercado
    asking = Decimal("1500.00")
    market = Decimal("2400.00")

    val = compute_economic_valuation(
        asking_price=asking,
        estimated_market_price=market,
        market_estimate_low=Decimal("2100.00"),
        market_estimate_high=Decimal("2700.00"),
        number_of_comparables=18,
        market_confidence_score=Decimal("0.85"),
        known_issues_repair_min=Decimal("100.00"),
        known_issues_repair_max=Decimal("400.00"),
        config={
            "fast_sale_discount_ratio": 0.88,
            "preparation_cost_default": 200.0,
            "transfer_tax_ratio": 0.04,
            "transfer_fee_dgt": 55.70,
            "target_roi_min": 25.0,
        },
    )

    # ITP España 4% sobre 1500 = 60.00; transferencia = 60.00 + 55.70 = 115.70
    assert val["estimated_tax"] == Decimal("60.00")
    assert val["estimated_transfer_cost"] == Decimal("115.70")
    assert val["estimated_preparation_cost"] == Decimal("200.00")

    # Coste total: 1500 + 115.70 + 200 + repair
    # Min repair: 100 -> 1915.70
    # Max repair: 400 -> 2215.70
    assert val["estimated_total_cost_min"] == Decimal("1915.70")
    assert val["estimated_total_cost_max"] == Decimal("2215.70")

    # Fast sale: min(low=2100, 2400*0.88=2112) = 2100.00
    assert val["estimated_fast_sale_price"] == Decimal("2100.00")

    # Margen:
    # Margin min: 2100 - 2215.70 = -115.70
    # Margin max: 2100 - 1915.70 = 184.30
    assert val["estimated_margin_min"] == Decimal("-115.70")
    assert val["estimated_margin_max"] == Decimal("184.30")

    # Target purchase price debe ser positivo
    assert val["target_purchase_price"] > Decimal("0.00")

    # Confianza alta por 18 comparables y score 0.85
    assert val["confidence_level"] == ConfidenceLevel.HIGH


@pytest.mark.unit
def test_economic_valuation_no_market_estimate() -> None:
    val = compute_economic_valuation(
        asking_price=Decimal("1800.00"),
        estimated_market_price=None,
        market_estimate_low=None,
        market_estimate_high=None,
        number_of_comparables=0,
    )
    assert val["estimated_market_price"] is None
    assert val["estimated_fast_sale_price"] is None
    assert val["estimated_margin_min"] is None
    assert val["estimated_margin_max"] is None
    assert val["target_purchase_price"] is None
    assert val["confidence_level"] == ConfidenceLevel.LOW
    assert val["estimated_total_cost_min"] > Decimal("1800.00")
