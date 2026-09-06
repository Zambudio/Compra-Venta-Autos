"""Estimación determinista de precio de mercado basada en comparables reales (Plan Maestro §20)."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from app.listings.vocab import canonical_brand
from app.vehicles.vocab import MarketEstimateMethod


@dataclass(frozen=True)
class MarketEstimateResult:
    estimated_amount: Decimal
    low_amount: Decimal
    high_amount: Decimal
    currency: str
    method: MarketEstimateMethod
    number_of_comparables: int
    confidence_score: Decimal


def _percentile(sorted_data: list[Decimal], p: float) -> Decimal:
    """Calcula el percentil p (0.0 a 1.0) sobre una lista ordenada de Decimal."""
    n = len(sorted_data)
    if n == 1:
        return sorted_data[0]
    k = (n - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    d0 = sorted_data[int(f)] * Decimal(str(c - k))
    d1 = sorted_data[int(c)] * Decimal(str(k - f))
    return (d0 + d1).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def estimate_market_price(
    subject: Mapping[str, Any],
    pool: Sequence[Mapping[str, Any]],
) -> MarketEstimateResult:
    """Estima el valor de mercado analizando comparables homogéneos con filtro IQR."""
    target_brand = canonical_brand(str(subject.get("brand", "")))
    target_model = str(subject.get("model", "")).strip().lower()
    target_fuel = str(subject.get("fuel_type", "")).upper()
    target_year = int(subject.get("year", 0))
    target_km = float(subject.get("mileage_km", 0))
    subject_price = Decimal(str(subject.get("price_amount", "0.00")))

    # 1. Filtrar candidatos comparables
    comparables: list[Decimal] = []
    for item in pool:
        item_brand = canonical_brand(str(item.get("brand", "")))
        if not item_brand or item_brand != target_brand:
            continue

        item_model = str(item.get("model", "")).strip().lower()
        if item_model != target_model:
            continue

        item_fuel = str(item.get("fuel_type", "")).upper()
        if target_fuel and item_fuel and target_fuel != item_fuel:
            continue

        item_year = int(item.get("year", 0))
        if abs(item_year - target_year) > 2:
            continue

        item_km = float(item.get("mileage_km", 0))
        km_diff = abs(item_km - target_km)
        if target_km > 0:
            if km_diff / target_km > 0.40 and km_diff > 40000:
                continue

        p = Decimal(str(item.get("price_amount", "0")))
        if p > Decimal("0"):
            comparables.append(p)

    n_raw = len(comparables)

    # Si no hay comparables suficientes, se ofrece estimación base con baja confianza
    if n_raw == 0:
        low = (subject_price * Decimal("0.85")).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        high = (subject_price * Decimal("1.15")).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        return MarketEstimateResult(
            estimated_amount=subject_price,
            low_amount=low,
            high_amount=high,
            currency="EUR",
            method=MarketEstimateMethod.COMPARABLES_MEDIAN_IQR,
            number_of_comparables=0,
            confidence_score=Decimal("0.100"),
        )

    comparables.sort()

    # 2. Filtrar outliers mediante rango intercuartil (IQR) si hay al menos 4 datos
    filtered_prices = comparables
    if n_raw >= 4:
        q1 = _percentile(comparables, 0.25)
        q3 = _percentile(comparables, 0.75)
        iqr = q3 - q1
        lower_bound = q1 - (iqr * Decimal("1.5"))
        upper_bound = q3 + (iqr * Decimal("1.5"))
        filtered = [p for p in comparables if lower_bound <= p <= upper_bound]
        if filtered:
            filtered_prices = filtered

    n = len(filtered_prices)
    median = _percentile(filtered_prices, 0.50)

    if n >= 4:
        low = _percentile(filtered_prices, 0.25)
        high = _percentile(filtered_prices, 0.75)
        # Asegurar amplitud mínima coherente
        if low == high:
            low = (median * Decimal("0.90")).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
            high = (median * Decimal("1.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    else:
        low = (min(filtered_prices) * Decimal("0.95")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_EVEN
        )
        high = (max(filtered_prices) * Decimal("1.05")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_EVEN
        )

    # 3. Cálculo de confianza estadística
    # Factor tamaño de muestra (escala hasta saturar en ~15 comparables)
    size_factor = min(1.0, n / 12.0)

    # Factor de homogeneidad (menor dispersión relativa da mayor confianza)
    dispersion_ratio = float((high - low) / median) if median > 0 else 0.5
    dispersion_factor = max(0.5, 1.0 - (dispersion_ratio * 0.5))

    calculated_confidence = size_factor * dispersion_factor
    # Clamped entre 0.200 y 0.900 (nunca 1.000 para no dar falsa certeza)
    clamped_conf = max(0.200, min(0.900, calculated_confidence))
    confidence_score = Decimal(str(clamped_conf)).quantize(
        Decimal("0.001"), rounding=ROUND_HALF_EVEN
    )

    return MarketEstimateResult(
        estimated_amount=median,
        low_amount=low,
        high_amount=high,
        currency="EUR",
        method=MarketEstimateMethod.COMPARABLES_MEDIAN_IQR,
        number_of_comparables=n,
        confidence_score=confidence_score,
    )
