"""Tests unitarios para el motor de scoring determinista (Fase 5)."""

from decimal import Decimal

import pytest

from app.scoring.engine import (
    compute_age_score,
    compute_condition_score,
    compute_history_score,
    compute_liquidity_score,
    compute_listing_age_score,
    compute_mechanical_risk_score,
    compute_mileage_score,
    compute_price_score,
    compute_reliability_score,
    evaluate_opportunity_score,
)
from app.scoring.vocab import DEFAULT_SCORING_WEIGHTS, SellerPressureLevel


@pytest.mark.unit
def test_price_score_no_market_data() -> None:
    score, exp, flags = compute_price_score(
        asking_price=Decimal("2000.00"),
        market_median=None,
        market_low=None,
        market_high=None,
    )
    assert score == Decimal("50.00")
    assert "NO_MARKET_DATA" in flags
    assert "Sin estimación de mercado" in exp


@pytest.mark.unit
def test_price_score_bargain_and_overpriced() -> None:
    # 35% por debajo de la mediana
    score_bargain, exp_b, flags_b = compute_price_score(
        asking_price=Decimal("1300.00"),
        market_median=Decimal("2000.00"),
        market_low=Decimal("1700.00"),
        market_high=Decimal("2400.00"),
    )
    assert score_bargain == Decimal("100.00")
    assert "BARGAIN_PRICE" in flags_b

    # 40% por encima de la mediana
    score_over, exp_o, flags_o = compute_price_score(
        asking_price=Decimal("2800.00"),
        market_median=Decimal("2000.00"),
        market_low=Decimal("1700.00"),
        market_high=Decimal("2400.00"),
    )
    assert score_over == Decimal("0.00")
    assert "OVERPRICED" in flags_o


@pytest.mark.unit
def test_reliability_score_classifications() -> None:
    score_white, _, flags_w = compute_reliability_score("WHITELIST")
    assert score_white == Decimal("100.00")
    assert "WHITELIST_ENGINE" in flags_w

    score_watch, _, flags_wa = compute_reliability_score("WATCHLIST")
    assert score_watch == Decimal("35.00")
    assert "WATCHLIST_ENGINE" in flags_wa

    score_black, _, flags_b = compute_reliability_score("BLACKLIST")
    assert score_black == Decimal("0.00")
    assert "BLACKLIST_ENGINE" in flags_b

    score_unk, _, _ = compute_reliability_score("UNKNOWN")
    assert score_unk == Decimal("60.00")

    score_none, _, _ = compute_reliability_score(None)
    assert score_none == Decimal("60.00")


@pytest.mark.unit
def test_liquidity_score_models() -> None:
    score_ibiza, _, flags_i = compute_liquidity_score("SEAT", "Ibiza 1.9 TDI", "diesel")
    assert score_ibiza == Decimal("100.00")
    assert "HIGH_LIQUIDITY" in flags_i

    score_clio, _, flags_c = compute_liquidity_score("Renault", "Clio 1.2", "gasolina")
    assert score_clio == Decimal("100.00")

    score_750, _, flags_7 = compute_liquidity_score("BMW", "750i V8", "gasolina")
    assert score_750 == Decimal("25.00")
    assert "LOW_LIQUIDITY" in flags_7

    score_std, _, _ = compute_liquidity_score("Fiat", "Sedici", "diesel")
    assert score_std == Decimal("70.00")


@pytest.mark.unit
def test_mechanical_risk_score_and_mitigations() -> None:
    # Caso 1: Sin problemas conocidos
    s1, _, _ = compute_mechanical_risk_score(
        known_issues_count=0,
        has_recall_campaign=False,
        max_severity=None,
        repair_cost_max=Decimal("0.00"),
        mitigations_count=0,
    )
    assert s1 == Decimal("100.00")

    # Caso 2: Problema crítico con recall
    s2, _, flags2 = compute_mechanical_risk_score(
        known_issues_count=2,
        has_recall_campaign=True,
        max_severity="CRITICAL",
        repair_cost_max=Decimal("2500.00"),
        mitigations_count=0,
    )
    # 100 - 35 (recall) - 40 (critical) - 20 (cost >= 2000) = 5
    assert s2 == Decimal("5.00")
    assert "HAS_RECALL" in flags2
    assert "CRITICAL_RISK" in flags2

    # Caso 3: Mismo problema pero con mitigación demostrada
    s3, _, flags3 = compute_mechanical_risk_score(
        known_issues_count=2,
        has_recall_campaign=True,
        max_severity="CRITICAL",
        repair_cost_max=Decimal("2500.00"),
        mitigations_count=1,
    )
    # 5 + 20 = 25
    assert s3 == Decimal("25.00")
    assert "MITIGATED_RISKS" in flags3


@pytest.mark.unit
def test_mileage_score_curves() -> None:
    # Sin km
    s_none, _, flags_n = compute_mileage_score(None, 2012, "diesel")
    assert s_none == Decimal("45.00")
    assert "NO_MILEAGE" in flags_n

    # Km muy bajo
    s_low, _, flags_l = compute_mileage_score(75000, 2012, "gasolina")
    assert s_low == Decimal("100.00")
    assert "LOW_MILEAGE" in flags_l

    # Km moderado
    s_med, _, _ = compute_mileage_score(130000, 2012, "diesel")
    assert s_med == Decimal("85.00")

    # Km muy alto
    s_high, _, flags_h = compute_mileage_score(340000, 2008, "diesel")
    assert s_high == Decimal("15.00")
    assert "HIGH_MILEAGE" in flags_h


@pytest.mark.unit
def test_age_score_curves() -> None:
    s_opt, _, _ = compute_age_score(2015)
    assert s_opt == Decimal("90.00")

    s_recent, _, _ = compute_age_score(2022)
    assert s_recent == Decimal("100.00")

    s_old, _, flags_o = compute_age_score(1995)
    assert s_old == Decimal("25.00")
    assert "VERY_OLD" in flags_o

    s_none, _, _ = compute_age_score(None)
    assert s_none == Decimal("50.00")


@pytest.mark.unit
def test_history_score_variations() -> None:
    # 2 rebajas de precio
    s_drop2, _, flags_d = compute_history_score(
        snapshots_count=3, reductions_count=2, price_increases_count=0
    )
    assert s_drop2 == Decimal("95.00")
    assert "PRICE_DROPPED_MULTIPLE" in flags_d

    # 1 rebaja de precio
    s_drop1, _, flags_d1 = compute_history_score(
        snapshots_count=2, reductions_count=1, price_increases_count=0
    )
    assert s_drop1 == Decimal("85.00")
    assert "PRICE_DROPPED" in flags_d1

    # Subida de precio
    s_inc, _, flags_i = compute_history_score(
        snapshots_count=2, reductions_count=0, price_increases_count=1
    )
    assert s_inc == Decimal("45.00")
    assert "PRICE_INCREASED" in flags_i


@pytest.mark.unit
def test_condition_score_keywords() -> None:
    # Anuncio con factores positivos
    pos_desc = (
        "Coche en perfecto estado, libro de revisiones al día, "
        "ITV en vigor recién pasada, distribución cambiada con factura."
    )
    s_pos, exp_p, _ = compute_condition_score("SEAT Ibiza", pos_desc)
    assert s_pos >= Decimal("85.00")
    assert "Factores favorables" in exp_p

    # Anuncio con avería declarada
    neg_desc = "Vehículo para piezas, averiado, fallo motor no arranca, posible junta de culata."
    s_neg, exp_n, flags_n = compute_condition_score("Peugeot 207", neg_desc)
    assert s_neg <= Decimal("20.00")
    assert "DEFECT_REPORTED" in flags_n
    assert "Defectos detectados" in exp_n

    # Anuncio vacío
    s_empty, _, _ = compute_condition_score(None, None)
    assert s_empty == Decimal("60.00")


@pytest.mark.unit
def test_listing_age_score() -> None:
    s_rec, _, _ = compute_listing_age_score(2, SellerPressureLevel.LOW)
    assert s_rec == Decimal("50.00")

    s_mat, _, _ = compute_listing_age_score(35, SellerPressureLevel.MEDIUM)
    assert s_mat == Decimal("85.00")

    s_high, _, flags_h = compute_listing_age_score(65, SellerPressureLevel.HIGH)
    assert s_high == Decimal("100.00")
    assert "HIGH_NEGOTIATION_POWER" in flags_h


@pytest.mark.unit
def test_evaluate_opportunity_score_full_aggregation() -> None:
    res = evaluate_opportunity_score(
        weights=DEFAULT_SCORING_WEIGHTS,
        asking_price=Decimal("1800.00"),
        market_median=Decimal("2400.00"),
        market_low=Decimal("2100.00"),
        market_high=Decimal("2800.00"),
        classification_status="WHITELIST",
        brand="SEAT",
        model="Ibiza",
        fuel_type="diesel",
        known_issues_count=0,
        has_recall_campaign=False,
        max_severity=None,
        repair_cost_max=Decimal("0.00"),
        mitigations_count=0,
        mileage_km=140000,
        year=2012,
        snapshots_count=2,
        price_reductions=1,
        price_increases=0,
        title="SEAT Ibiza 1.9 TDI ITV al día",
        description="Distribución cambiada con factura, en garaje.",
        days_on_market=22,
        seller_pressure_level=SellerPressureLevel.MEDIUM,
    )

    assert Decimal("80.00") <= res["total_score"] <= Decimal("100.00")
    assert res["price_score"] >= Decimal("80.00")
    assert res["reliability_score"] == Decimal("100.00")
    assert res["liquidity_score"] == Decimal("100.00")
    assert res["mechanical_risk_score"] == Decimal("100.00")
    assert len(res["score_breakdown"]) == 9
    for comp in DEFAULT_SCORING_WEIGHTS:
        assert comp in res["score_breakdown"]
        item = res["score_breakdown"][comp]
        assert "score" in item
        assert "weight" in item
        assert "weighted_score" in item
        assert "explanation" in item
