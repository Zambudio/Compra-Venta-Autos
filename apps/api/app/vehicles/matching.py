"""Algoritmo determinista de matching y deduplicación asistida entre anuncios (Fase 3).

Reglas de compliance y privacidad (Plan Maestro §13, §32; R-03):
- CERO uso de matrículas ni teléfonos.
- Ponderación multicriterio explicable y determinista.
- Función pura sin efectos secundarios ni I/O.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from app.listings.vocab import Transmission, canonical_brand

_STOPWORDS = {
    "para",
    "este",
    "esta",
    "estos",
    "estas",
    "todo",
    "toda",
    "todos",
    "todas",
    "como",
    "pero",
    "coche",
    "auto",
    "vehiculo",
    "muy",
    "bien",
    "buen",
    "bueno",
    "buena",
    "perfecto",
    "estado",
    "ano",
    "anos",
}


@dataclass(frozen=True)
class MatchResult:
    confidence: Decimal
    reasons: dict[str, Any]


def _extract_tokens(text: str | None) -> set[str]:
    if not text:
        return set()
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    tokens = {t for t in cleaned.split() if len(t) >= 3 and t not in _STOPWORDS}
    return tokens


def _jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    if not set_a and not set_b:
        return 0.5
    if not set_a or not set_b:
        return 0.5
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def _string_similarity(str_a: str, str_b: str) -> float:
    tokens_a = _extract_tokens(str_a)
    tokens_b = _extract_tokens(str_b)
    if not tokens_a and not tokens_b:
        return 1.0 if str_a.strip().lower() == str_b.strip().lower() else 0.0
    return _jaccard_similarity(tokens_a, tokens_b)


def _relative_difference(val_a: float, val_b: float) -> float:
    max_val = max(abs(val_a), abs(val_b))
    if max_val == 0.0:
        return 0.0
    return abs(val_a - val_b) / max_val


def _score_relative_diff(diff: float) -> float:
    if diff <= 0.05:
        return 1.0
    if diff <= 0.15:
        return 0.7
    if diff <= 0.30:
        return 0.3
    return 0.0


def score_match(
    listing_a: Mapping[str, Any],
    listing_b: Mapping[str, Any],
) -> MatchResult:
    """Calcula la similitud y explicabilidad entre dos anuncios sin usar datos personales."""
    brand_a = canonical_brand(str(listing_a.get("brand", "")))
    brand_b = canonical_brand(str(listing_b.get("brand", "")))

    if not brand_a or not brand_b or brand_a != brand_b:
        return MatchResult(
            confidence=Decimal("0.000"),
            reasons={"brand_mismatch": True, "brand_a": brand_a, "brand_b": brand_b},
        )

    fuel_a = listing_a.get("fuel_type")
    fuel_b = listing_b.get("fuel_type")
    if fuel_a and fuel_b and fuel_a != fuel_b:
        return MatchResult(
            confidence=Decimal("0.000"),
            reasons={"fuel_type_mismatch": True, "fuel_a": str(fuel_a), "fuel_b": str(fuel_b)},
        )

    trans_a = listing_a.get("transmission")
    trans_b = listing_b.get("transmission")
    if (
        trans_a
        and trans_b
        and trans_a != Transmission.UNKNOWN
        and trans_b != Transmission.UNKNOWN
        and trans_a != trans_b
    ):
        return MatchResult(
            confidence=Decimal("0.000"),
            reasons={
                "transmission_mismatch": True,
                "transmission_a": str(trans_a),
                "transmission_b": str(trans_b),
            },
        )

    model_a = str(listing_a.get("model", ""))
    model_b = str(listing_b.get("model", ""))
    model_score = _string_similarity(model_a, model_b)

    year_a = int(listing_a.get("year", 0))
    year_b = int(listing_b.get("year", 0))
    year_diff = abs(year_a - year_b)
    if year_diff == 0:
        year_score = 1.0
    elif year_diff == 1:
        year_score = 0.5
    else:
        year_score = 0.0

    specs_score = 1.0 if fuel_a == fuel_b and trans_a == trans_b else 0.8

    km_a = float(listing_a.get("mileage_km", 0))
    km_b = float(listing_b.get("mileage_km", 0))
    km_diff = _relative_difference(km_a, km_b)
    mileage_score = _score_relative_diff(km_diff)

    p_a = float(Decimal(str(listing_a.get("price_amount", "0"))))
    p_b = float(Decimal(str(listing_b.get("price_amount", "0"))))
    price_diff = _relative_difference(p_a, p_b)
    price_score = _score_relative_diff(price_diff)

    prov_a = listing_a.get("province")
    prov_b = listing_b.get("province")
    if prov_a and prov_b:
        location_score = 1.0 if str(prov_a).strip().lower() == str(prov_b).strip().lower() else 0.0
    else:
        location_score = 0.5

    desc_a = listing_a.get("description")
    desc_b = listing_b.get("description")
    description_score = _jaccard_similarity(_extract_tokens(desc_a), _extract_tokens(desc_b))

    # Ponderaciones multicriterio deterministas
    base_score = (
        (model_score * 0.25)
        + (year_score * 0.20)
        + (specs_score * 0.15)
        + (mileage_score * 0.15)
        + (price_score * 0.10)
        + (location_score * 0.05)
        + (description_score * 0.10)
    )

    # Penalización de consistencia física: el mismo coche no puede divergir drásticamente
    consistency_factor = 1.0
    if km_diff > 0.25 or abs(km_a - km_b) > 25000:
        consistency_factor *= 0.6
    if price_diff > 0.35:
        consistency_factor *= 0.7
    if year_diff > 1:
        consistency_factor *= 0.2

    total_score = base_score * consistency_factor

    clamped = max(0.0, min(1.0, total_score))
    confidence_decimal = Decimal(str(clamped)).quantize(Decimal("0.001"), rounding=ROUND_HALF_EVEN)

    reasons: dict[str, Any] = {
        "brand": brand_a,
        "model": {"score": round(model_score, 3), "model_a": model_a, "model_b": model_b},
        "year": {"score": round(year_score, 3), "year_a": year_a, "year_b": year_b},
        "year_score": round(year_score, 3),
        "fuel_type": str(fuel_a),
        "transmission": str(trans_a),
        "mileage": {"score": round(mileage_score, 3), "diff_ratio": round(km_diff, 3)},
        "price": {"score": round(price_score, 3), "diff_ratio": round(price_diff, 3)},
        "location": {"score": round(location_score, 3)},
        "description": {"score": round(description_score, 3)},
    }

    return MatchResult(confidence=confidence_decimal, reasons=reasons)
