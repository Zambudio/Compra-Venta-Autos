"""Cálculo dinámico de histórico de precios y métricas temporales (Plan Maestro §12)."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from app.listings.vocab import ListingStatus
from app.vehicles.schemas import ListingHistoryMetrics, VehicleHistoryMetrics


def calculate_listing_history(snapshots: Sequence[Any]) -> ListingHistoryMetrics:
    """Calcula las métricas de evolución temporal a partir de los snapshots del anuncio."""
    if not snapshots:
        return ListingHistoryMetrics(
            initial_price=Decimal("0.00"),
            current_price=Decimal("0.00"),
            price_delta=Decimal("0.00"),
            price_delta_percentage=Decimal("0.00"),
            days_on_market=0,
            number_of_price_changes=0,
            is_relisted=False,
        )

    sorted_snaps = sorted(snapshots, key=lambda s: s.observed_at)
    first = sorted_snaps[0]
    last = sorted_snaps[-1]

    initial_price = Decimal(str(getattr(first, "price_amount", 0)))
    current_price = Decimal(str(getattr(last, "price_amount", 0)))
    price_delta = current_price - initial_price

    if initial_price > Decimal("0"):
        pct = (price_delta / initial_price) * Decimal("100")
        price_delta_percentage = pct.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    else:
        price_delta_percentage = Decimal("0.00")

    days_on_market = max(0, (last.observed_at - first.observed_at).days)

    price_changes = 0
    had_withdrawn = False
    is_relisted = False

    for i in range(len(sorted_snaps)):
        snap = sorted_snaps[i]
        status = getattr(snap, "status", ListingStatus.ACTIVE)
        if status == ListingStatus.WITHDRAWN:
            had_withdrawn = True
        elif had_withdrawn and status == ListingStatus.ACTIVE:
            is_relisted = True

        if i > 0:
            prev_price = Decimal(str(getattr(sorted_snaps[i - 1], "price_amount", 0)))
            curr_price = Decimal(str(getattr(snap, "price_amount", 0)))
            if prev_price != curr_price:
                price_changes += 1

    return ListingHistoryMetrics(
        initial_price=initial_price,
        current_price=current_price,
        price_delta=price_delta,
        price_delta_percentage=price_delta_percentage,
        days_on_market=days_on_market,
        number_of_price_changes=price_changes,
        is_relisted=is_relisted,
    )


def calculate_vehicle_history(
    listing_snapshots_list: Sequence[Sequence[Any]],
    current_prices: Sequence[Decimal] | None = None,
) -> VehicleHistoryMetrics:
    """Calcula las métricas consolidadas del histórico de un vehículo unificado."""
    all_snapshots = [s for sublist in listing_snapshots_list for s in sublist]
    if not all_snapshots:
        default_price = current_prices[0] if current_prices else Decimal("0.00")
        return VehicleHistoryMetrics(
            lowest_observed_price=default_price,
            highest_observed_price=default_price,
            current_min_price=default_price,
            days_on_market=0,
            total_price_changes=0,
        )

    all_sorted = sorted(all_snapshots, key=lambda s: s.observed_at)
    prices = [Decimal(str(getattr(s, "price_amount", 0))) for s in all_sorted]

    lowest_price = min(prices)
    highest_price = max(prices)
    current_min_price = min(current_prices) if current_prices else lowest_price

    first_date = all_sorted[0].observed_at
    last_date = all_sorted[-1].observed_at
    days_on_market = max(0, (last_date - first_date).days)

    total_changes = 0
    for sublist in listing_snapshots_list:
        sub_history = calculate_listing_history(sublist)
        total_changes += sub_history.number_of_price_changes

    return VehicleHistoryMetrics(
        lowest_observed_price=lowest_price,
        highest_observed_price=highest_price,
        current_min_price=current_min_price,
        days_on_market=days_on_market,
        total_price_changes=total_changes,
    )
