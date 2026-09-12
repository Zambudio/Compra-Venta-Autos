"""Cálculo de valoración económica, intervalos de confianza y presión del vendedor (Fase 5).

Conforme al Plan Maestro (§19, §20, §23) y ADR-0015:
- Toda valoración se expresa con precisión Decimal (EUR).
- No se presentan certezas infalibles; se utilizan intervalos (min - max) y nivel de confianza.
- Los costes en España contemplan ITP (Impuesto de Transmisiones Patrimoniales) y tasas DGT.
- La presión del vendedor es determinista y no infiere circunstancias personales subjetivas.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.scoring.vocab import ConfidenceLevel, SellerPressureLevel


def _quantize_currency(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _quantize_percentage(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_seller_pressure(
    published_at: datetime | None,
    last_seen_at: datetime | None,
    snapshots: list[Any],
    current_price: Decimal,
) -> tuple[SellerPressureLevel, list[str], int, int, Decimal, Decimal]:
    """Calcula la presión objetiva del vendedor basada en días en venta y rebajas de precio.

    Devuelve: (level, reasons, days_on_market, reductions_count, reduction_amt, reduction_pct)
    """
    now = datetime.now(UTC)

    def _snap_time(s: Any) -> datetime:
        return getattr(s, "observed_at", getattr(s, "snapshot_at", now))

    ref_start = published_at or (_snap_time(snapshots[0]) if snapshots else now)
    ref_end = last_seen_at or now

    days_on_market = max(1, (ref_end.date() - ref_start.date()).days)

    reductions_count = 0
    initial_price = current_price

    if snapshots:
        sorted_snaps = sorted(snapshots, key=_snap_time)
        initial_price = sorted_snaps[0].price_amount
        prev_price = initial_price
        for snap in sorted_snaps[1:]:
            if snap.price_amount < prev_price:
                reductions_count += 1
            prev_price = snap.price_amount
        if current_price < prev_price:
            reductions_count += 1

    total_reduction_amount = max(Decimal("0.00"), initial_price - current_price)
    if initial_price > Decimal("0.00") and total_reduction_amount > Decimal("0.00"):
        total_reduction_pct = _quantize_percentage(
            (total_reduction_amount / initial_price) * Decimal("100.00")
        )
    else:
        total_reduction_pct = Decimal("0.00")

    reasons: list[str] = [f"{days_on_market} días publicado en el portal"]

    if reductions_count > 0:
        reasons.append(f"{reductions_count} reducciones de precio registradas")
        reasons.append(
            f"-{total_reduction_pct:.1f}% de rebaja acumulada "
            f"({initial_price} EUR -> {current_price} EUR)"
        )

    # Determinación determinista del nivel de presión (Plan Maestro §23)
    if days_on_market >= 45 and (reductions_count >= 2 or total_reduction_pct >= Decimal("15.00")):
        level = SellerPressureLevel.HIGH
        reasons.append("Alta presión: largo tiempo en mercado con reducciones sucesivas de precio")
    elif days_on_market >= 25 or reductions_count >= 1 or total_reduction_pct >= Decimal("8.00"):
        level = SellerPressureLevel.MEDIUM
        reasons.append("Presión moderada: tiempo relevante o rebaja de precio inicial")
    else:
        level = SellerPressureLevel.LOW
        reasons.append("Baja presión: publicación reciente o precio sin variaciones a la baja")

    return (
        level,
        reasons,
        days_on_market,
        reductions_count,
        _quantize_currency(total_reduction_amount),
        total_reduction_pct,
    )


def compute_economic_valuation(
    asking_price: Decimal,
    estimated_market_price: Decimal | None,
    market_estimate_low: Decimal | None,
    market_estimate_high: Decimal | None,
    number_of_comparables: int = 0,
    market_confidence_score: Decimal = Decimal("0.00"),
    known_issues_repair_min: Decimal = Decimal("0.00"),
    known_issues_repair_max: Decimal = Decimal("0.00"),
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Calcula la valoración económica completa en intervalos de confianza (Plan Maestro §19)."""
    cfg = config or {}
    fast_sale_ratio = Decimal(str(cfg.get("fast_sale_discount_ratio", "0.88")))
    prep_cost_val = Decimal(str(cfg.get("preparation_cost_default", "200.00")))
    tax_ratio = Decimal(str(cfg.get("transfer_tax_ratio", "0.04")))
    fee_dgt = Decimal(str(cfg.get("transfer_fee_dgt", "55.70")))
    target_roi_min_pct = Decimal(str(cfg.get("target_roi_min", "25.0")))

    # 1. Impuesto ITP y transferencia DGT en España
    estimated_tax = _quantize_currency(asking_price * tax_ratio)
    estimated_transfer_cost = _quantize_currency(estimated_tax + fee_dgt)
    estimated_preparation_cost = _quantize_currency(prep_cost_val)

    # 2. Reparación
    repair_min = _quantize_currency(known_issues_repair_min)
    repair_max = _quantize_currency(known_issues_repair_max)

    # 3. Costes totales acumulados (mínimo y máximo)
    total_cost_min = _quantize_currency(
        asking_price + estimated_transfer_cost + estimated_preparation_cost + repair_min
    )
    total_cost_max = _quantize_currency(
        asking_price + estimated_transfer_cost + estimated_preparation_cost + repair_max
    )

    # 4. Estimación de venta rápida (Fast Sale)
    estimated_fast_sale_price: Decimal | None = None
    estimated_margin_min: Decimal | None = None
    estimated_margin_max: Decimal | None = None
    estimated_roi_min: Decimal | None = None
    estimated_roi_max: Decimal | None = None
    target_purchase_price: Decimal | None = None

    if estimated_market_price is not None and estimated_market_price > Decimal("0.00"):
        # Precio de salida rápida: mínimo entre percentil bajo o descuento sobre mediana
        calc_fast = estimated_market_price * fast_sale_ratio
        if market_estimate_low is not None and market_estimate_low > Decimal("0.00"):
            estimated_fast_sale_price = _quantize_currency(min(market_estimate_low, calc_fast))
        else:
            estimated_fast_sale_price = _quantize_currency(calc_fast)

        # Margen: Fast Sale - Coste Total
        estimated_margin_min = _quantize_currency(estimated_fast_sale_price - total_cost_max)
        estimated_margin_max = _quantize_currency(estimated_fast_sale_price - total_cost_min)

        # ROI: (Margen / Coste Total) * 100
        if total_cost_max > Decimal("0.00"):
            estimated_roi_min = _quantize_percentage(
                (estimated_margin_min / total_cost_max) * Decimal("100.00")
            )
        if total_cost_min > Decimal("0.00"):
            estimated_roi_max = _quantize_percentage(
                (estimated_margin_max / total_cost_min) * Decimal("100.00")
            )

        # Precio objetivo de compra (Target Purchase Price) para alcanzar ROI objetivo
        # fast_sale / (1 + target_roi/100) = max_total_cost_tolerable
        repair_avg = (repair_min + repair_max) / Decimal("2.0")
        max_total_tolerable = estimated_fast_sale_price / (
            Decimal("1.0") + (target_roi_min_pct / Decimal("100.0"))
        )
        calculated_target = (
            max_total_tolerable - estimated_transfer_cost - estimated_preparation_cost - repair_avg
        )
        target_purchase_price = _quantize_currency(max(Decimal("0.00"), calculated_target))

    # 5. Nivel de confianza objetivo (Plan Maestro §20)
    if (
        estimated_market_price is not None
        and number_of_comparables >= 15
        and market_confidence_score >= Decimal("0.70")
    ):
        confidence_level = ConfidenceLevel.HIGH
    elif estimated_market_price is not None and number_of_comparables >= 5:
        confidence_level = ConfidenceLevel.MEDIUM
    else:
        confidence_level = ConfidenceLevel.LOW

    return {
        "asking_price": _quantize_currency(asking_price),
        "estimated_market_price": (
            _quantize_currency(estimated_market_price)
            if estimated_market_price is not None
            else None
        ),
        "estimated_fast_sale_price": estimated_fast_sale_price,
        "target_purchase_price": target_purchase_price,
        "estimated_transfer_cost": estimated_transfer_cost,
        "estimated_tax": estimated_tax,
        "estimated_repair_min": repair_min,
        "estimated_repair_max": repair_max,
        "estimated_preparation_cost": estimated_preparation_cost,
        "estimated_total_cost_min": total_cost_min,
        "estimated_total_cost_max": total_cost_max,
        "estimated_margin_min": estimated_margin_min,
        "estimated_margin_max": estimated_margin_max,
        "estimated_roi_min": estimated_roi_min,
        "estimated_roi_max": estimated_roi_max,
        "confidence_level": confidence_level,
    }
