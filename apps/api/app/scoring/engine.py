"""Motor de scoring 100% determinista, explicable y versionado (Fase 5).

Conforme al Plan Maestro (§18):
- Cero Machine Learning en el MVP.
- Cada puntuación explica con exactitud "por qué este coche tiene X puntos".
- Ponderación configurable mediante ScoringProfileVersion inmutable.
- 9 componentes obligatorios que suman 1.000 (100%).
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.scoring.vocab import (
    DEFAULT_SCORING_WEIGHTS,
    ScoringComponent,
    SellerPressureLevel,
)


def _quantize_score(value: Decimal) -> Decimal:
    clamped = max(Decimal("0.00"), min(Decimal("100.00"), value))
    return clamped.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# Conjunto de modelos de altísima liquidez en España (segmento B/C popular)
HIGH_LIQUIDITY_MODELS = {
    "ibiza",
    "leon",
    "golf",
    "polo",
    "clio",
    "megane",
    "206",
    "207",
    "208",
    "307",
    "308",
    "focus",
    "fiesta",
    "corsa",
    "astra",
    "c3",
    "c4",
    "yaris",
    "corolla",
    "auris",
    "punto",
    "sandero",
}

LOW_LIQUIDITY_SEGMENTS = {
    "730",
    "740",
    "750",
    "a8",
    "s320",
    "s350",
    "s500",
    "phaeton",
    "touareg",
    "cayenne",
    "range rover",
    "cherokee",
}

POSITIVE_CONDITION_PATTERNS = [
    (
        r"\bitv\s+(?:en\s+vigor|al\s+d[ií]a|reci[eé]n(?:\s+pasada)?)\b",
        12,
        "ITV en vigor / recién pasada",
    ),
    (
        r"\b(?:distribuci[oó]n|correa|cadena)\s+(?:hecha|cambiada|nueva|al\s+d[ií]a)\b",
        15,
        "Distribución recién cambiada",
    ),
    (r"\blibro\s+de\s+(?:mantenimiento|revisiones)\b", 10, "Libro de revisiones documentado"),
    (r"\b[uú]nico\s+propietario|un\s+solo\s+due[ñn]o\b", 10, "Único propietario"),
    (r"\bsiempre\s+en\s+garaje\b", 8, "Vehículo en garaje"),
    (
        r"\bmantenimiento\s+al\s+d[ií]a|revisi[oó]n\s+reci[eé]n\s+hecha\b",
        10,
        "Mantenimiento al día",
    ),
    (r"\bneum[aá]ticos\s+(?:nuevos|al\s+90%|al\s+80%)\b", 6, "Neumáticos en buen estado"),
]

NEGATIVE_CONDITION_PATTERNS = [
    (r"\b(?:para\s+piezas|para\s+repuestos|despiece)\b", 60, "Vehículo destinado a despiece"),
    (
        r"\b(?:averiado|con\s+aver[ií]a|fallo\s+de\s+motor|no\s+arranca)\b",
        45,
        "Avería mecánica explícita",
    ),
    (r"\bjunta\s+de\s+culata\b", 50, "Problema grave de junta de culata"),
    (
        r"\bcaja\s+(?:de\s+cambios\s+)?rota|falla\s+el\s+cambio\b",
        45,
        "Fallo grave en caja de cambios",
    ),
    (r"\b(?:golpe|siniestro|accidente)\b", 40, "Daños por accidente o golpe"),
    (r"\bsin\s+itv|itv\s+caducada|itv\s+desfavorable\b", 20, "Sin ITV en vigor"),
]


def compute_price_score(
    asking_price: Decimal,
    market_median: Decimal | None,
    market_low: Decimal | None,
    market_high: Decimal | None,
) -> tuple[Decimal, str, list[str]]:
    """1. Precio respecto al mercado (25%)."""
    flags: list[str] = []
    if market_median is None or market_median <= Decimal("0.00"):
        flags.append("NO_MARKET_DATA")
        return (
            Decimal("50.00"),
            (
                "Sin estimación de mercado fiable disponible en comparables "
                "(puntuación neutra asignada)."
            ),
            flags,
        )

    ratio = asking_price / market_median

    if ratio <= Decimal("0.70"):
        score = Decimal("100.00")
        diff_pct = (Decimal("1.00") - ratio) * 100
        explanation = (
            f"Precio excepcional: {asking_price:.2f} EUR está un "
            f"{diff_pct:.1f}% por debajo de la mediana ({market_median:.2f} EUR)."
        )
        flags.append("BARGAIN_PRICE")
    elif ratio <= Decimal("0.85"):
        # Entre 0.70 y 0.85: lineal 100 a 80
        progress = (ratio - Decimal("0.70")) / Decimal("0.15")
        score = Decimal("100.00") - progress * Decimal("20.00")
        diff_pct = (Decimal("1.00") - ratio) * 100
        explanation = (
            f"Precio ventajoso: {asking_price:.2f} EUR está un "
            f"{diff_pct:.1f}% por debajo del mercado ({market_median:.2f} EUR)."
        )
    elif ratio <= Decimal("1.00"):
        # Entre 0.85 y 1.00: lineal 80 a 60
        progress = (ratio - Decimal("0.85")) / Decimal("0.15")
        score = Decimal("80.00") - progress * Decimal("20.00")
        explanation = (
            f"Precio alineado o por debajo de la mediana de mercado ({market_median:.2f} EUR)."
        )
    elif ratio <= Decimal("1.15"):
        # Entre 1.00 y 1.15: lineal 60 a 30
        progress = (ratio - Decimal("1.00")) / Decimal("0.15")
        score = Decimal("60.00") - progress * Decimal("30.00")
        diff_pct = (ratio - Decimal("1.00")) * 100
        explanation = f"Precio moderadamente superior a la mediana (+{diff_pct:.1f}%)."
    else:
        # Superior a 1.15: cae a 0 en ratio >= 1.30
        progress = min(Decimal("1.00"), (ratio - Decimal("1.15")) / Decimal("0.15"))
        score = Decimal("30.00") - progress * Decimal("30.00")
        diff_pct = (ratio - Decimal("1.00")) * 100
        explanation = f"Precio significativamente por encima de la mediana (+{diff_pct:.1f}%)."
        flags.append("OVERPRICED")

    return _quantize_score(score), explanation, flags


def compute_reliability_score(
    classification_status: str | None,
) -> tuple[Decimal, str, list[str]]:
    """2. Fiabilidad de motor basada en Knowledge Base (20%)."""
    flags: list[str] = []
    status = (classification_status or "").upper()

    if status == "WHITELIST":
        score = Decimal("100.00")
        explanation = (
            "Mecánica recomendada (WHITELIST): fiabilidad contrastada sin fallos sistémicos."
        )
        flags.append("WHITELIST_ENGINE")
    elif status == "WATCHLIST":
        score = Decimal("35.00")
        explanation = (
            "Mecánica bajo observación (WATCHLIST): presenta problemas conocidos a revisar."
        )
        flags.append("WATCHLIST_ENGINE")
    elif status == "BLACKLIST":
        score = Decimal("0.00")
        explanation = (
            "Mecánica desaconsejada (BLACKLIST): fallos catastróficos o campañas oficiales."
        )
        flags.append("BLACKLIST_ENGINE")
    else:
        score = Decimal("60.00")
        explanation = "Mecánica no catalogada (UNKNOWN): sin incidencias críticas documentadas."

    return _quantize_score(score), explanation, flags


def compute_liquidity_score(
    brand: str,
    model: str,
    fuel_type: str | None,
) -> tuple[Decimal, str, list[str]]:
    """3. Liquidez estimada en el mercado de ocasión español (15%)."""
    flags: list[str] = []
    norm_model = (model or "").lower().strip()
    norm_fuel = (fuel_type or "").lower().strip()

    # Comprobación de modelos populares de gran rotación
    is_high_liquidity = any(hm in norm_model for hm in HIGH_LIQUIDITY_MODELS)
    is_low_liquidity = any(lm in norm_model for lm in LOW_LIQUIDITY_SEGMENTS)

    if is_high_liquidity:
        score = Decimal("95.00")
        if norm_fuel in ("diesel", "gasolina"):
            score = Decimal("100.00")
        explanation = (
            f"Alta liquidez: modelo utilitario/compacto ({brand} {model}) "
            f"con rápida salida comercial."
        )
        flags.append("HIGH_LIQUIDITY")
    elif is_low_liquidity:
        score = Decimal("25.00")
        explanation = (
            f"Baja liquidez: vehículo de gran cilindrada/premium ({brand} {model}) "
            f"de lenta reventa."
        )
        flags.append("LOW_LIQUIDITY")
    else:
        score = Decimal("70.00")
        explanation = (
            f"Liquidez estándar: modelo comercial con rotación habitual ({brand} {model})."
        )

    return _quantize_score(score), explanation, flags


def compute_mechanical_risk_score(
    known_issues_count: int,
    has_recall_campaign: bool,
    max_severity: str | None,
    repair_cost_max: Decimal,
    mitigations_count: int,
) -> tuple[Decimal, str, list[str]]:
    """4. Riesgo mecánico acumulado (15%)."""
    flags: list[str] = []
    base = Decimal("100.00")

    penalties = Decimal("0.00")
    if has_recall_campaign:
        penalties += Decimal("35.00")
        flags.append("HAS_RECALL")

    sev = (max_severity or "").upper()
    if sev == "CRITICAL":
        penalties += Decimal("40.00")
        flags.append("CRITICAL_RISK")
    elif sev == "HIGH":
        penalties += Decimal("25.00")
        flags.append("HIGH_RISK")
    elif sev == "MEDIUM":
        penalties += Decimal("15.00")
    elif sev == "LOW":
        penalties += Decimal("5.00")

    if repair_cost_max >= Decimal("2000.00"):
        penalties += Decimal("20.00")
    elif repair_cost_max >= Decimal("1000.00"):
        penalties += Decimal("10.00")

    # Mitigaciones acreditadas devuelven puntos
    recovery = Decimal("0.00")
    if mitigations_count > 0:
        recovery = min(Decimal("35.00"), Decimal(mitigations_count) * Decimal("20.00"))
        flags.append("MITIGATED_RISKS")

    score = base - penalties + recovery
    explanation = (
        f"{known_issues_count} afecciones mecánicas conocidas "
        f"(severidad máx: {sev or 'ninguna'}), "
        f"coste estimado máx: {repair_cost_max:.2f} EUR. "
        f"{mitigations_count} mitigaciones demostradas."
    )
    return _quantize_score(score), explanation, flags


def compute_mileage_score(
    mileage_km: int | None,
    year: int | None,
    fuel_type: str | None,
) -> tuple[Decimal, str, list[str]]:
    """5. Kilometraje real frente al esperado por combustible y edad (8%)."""
    flags: list[str] = []
    if mileage_km is None:
        flags.append("NO_MILEAGE")
        return (
            Decimal("45.00"),
            "Kilometraje no especificado en el anuncio (penalización preventiva).",
            flags,
        )

    now_year = datetime.now(UTC).year
    car_year = year or (now_year - 12)
    age = max(1, now_year - car_year)

    annual_expected = 16000 if (fuel_type or "").lower() == "diesel" else 11000
    expected_km = age * annual_expected

    if mileage_km <= 90000:
        score = Decimal("100.00")
        explanation = (
            f"Kilometraje muy bajo ({mileage_km:,} km para {age} años, "
            f"esperado ~{expected_km:,} km)."
        )
        flags.append("LOW_MILEAGE")
    elif mileage_km <= 150000:
        score = Decimal("85.00")
        explanation = (
            f"Kilometraje moderado y favorable ({mileage_km:,} km, esperado ~{expected_km:,} km)."
        )
    elif mileage_km <= 210000:
        score = Decimal("65.00")
        explanation = f"Kilometraje coherente con la edad ({mileage_km:,} km para {age} años)."
    elif mileage_km <= 280000:
        score = Decimal("40.00")
        explanation = (
            f"Kilometraje elevado ({mileage_km:,} km). "
            f"Desgaste previsible en componentes de suspensión y motor."
        )
    else:
        score = Decimal("15.00")
        explanation = f"Kilometraje muy severo ({mileage_km:,} km). Alto riesgo de fatiga mecánica."
        flags.append("HIGH_MILEAGE")

    return _quantize_score(score), explanation, flags


def compute_age_score(year: int | None) -> tuple[Decimal, str, list[str]]:
    """6. Edad y curva de depreciación (5%)."""
    flags: list[str] = []
    if year is None:
        return Decimal("50.00"), "Año de matriculación no disponible.", flags

    now_year = datetime.now(UTC).year
    age = max(0, now_year - year)

    if age <= 7:
        score = Decimal("100.00")
        explanation = f"Vehículo seminuevo/reciente ({year}, {age} años de antigüedad)."
    elif age <= 13:
        # Entre 8 y 13 años: rango óptimo de compra-venta económica (<3.000€)
        score = Decimal("90.00")
        explanation = (
            f"Rango óptimo de compra-venta ({year}, {age} años): "
            f"mecánica accesible y valor residual estable."
        )
    elif age <= 18:
        score = Decimal("75.00")
        explanation = (
            f"Antigüedad intermedia ({year}, {age} años): "
            f"mantenimiento sencillo con desgaste habitual."
        )
    elif age <= 23:
        score = Decimal("50.00")
        explanation = (
            f"Antigüedad notable ({year}, {age} años): "
            f"posibles restricciones medioambientales (etiqueta)."
        )
    else:
        score = Decimal("25.00")
        explanation = (
            f"Vehículo veterano ({year}, {age} años): riesgo de obsolescencia y recambios."
        )
        flags.append("VERY_OLD")

    return _quantize_score(score), explanation, flags


def compute_history_score(
    snapshots_count: int,
    reductions_count: int,
    price_increases_count: int = 0,
) -> tuple[Decimal, str, list[str]]:
    """7. Historial y trayectoria en el portal (5%)."""
    flags: list[str] = []
    base = Decimal("70.00")

    if price_increases_count > 0:
        base -= Decimal("25.00")
        flags.append("PRICE_INCREASED")
        explanation = (
            f"Historial irregular: el vendedor ha incrementado el precio "
            f"{price_increases_count} vez/veces."
        )
    elif reductions_count >= 2:
        base += Decimal("25.00")
        flags.append("PRICE_DROPPED_MULTIPLE")
        explanation = (
            f"Historial favorable: {reductions_count} reducciones consecutivas "
            f"de precio observadas."
        )
    elif reductions_count == 1:
        base += Decimal("15.00")
        flags.append("PRICE_DROPPED")
        explanation = "Historial con bajada de precio registrada durante el seguimiento."
    else:
        explanation = (
            f"Historial estable sin variaciones bruscas de precio "
            f"({snapshots_count} capturas observadas)."
        )

    return _quantize_score(base), explanation, flags


def compute_condition_score(
    title: str | None,
    description: str | None,
) -> tuple[Decimal, str, list[str]]:
    """8. Estado declarado en título y descripción (5%)."""
    flags: list[str] = []
    text = f"{title or ''} {description or ''}".lower()

    if not text.strip():
        return Decimal("60.00"), "Sin descripción detallada en el anuncio.", flags

    score = Decimal("65.00")
    positives_found: list[str] = []
    negatives_found: list[str] = []

    for pattern, bonus, label in POSITIVE_CONDITION_PATTERNS:
        if re.search(pattern, text):
            score += Decimal(bonus)
            positives_found.append(label)

    for pattern, penalty, label in NEGATIVE_CONDITION_PATTERNS:
        if re.search(pattern, text):
            score -= Decimal(penalty)
            negatives_found.append(label)
            flags.append("DEFECT_REPORTED")

    reasons: list[str] = []
    if positives_found:
        reasons.append(f"Factores favorables: {', '.join(positives_found)}")
    if negatives_found:
        reasons.append(f"Defectos detectados: {', '.join(negatives_found)}")
    if not reasons:
        reasons.append("Descripción estándar sin menciones técnicas destacadas")

    return _quantize_score(score), "; ".join(reasons), flags


def compute_listing_age_score(
    days_on_market: int,
    seller_pressure_level: SellerPressureLevel,
) -> tuple[Decimal, str, list[str]]:
    """9. Tiempo del anuncio y oportunidad de negociación (2%)."""
    flags: list[str] = []

    if days_on_market <= 4:
        score = Decimal("50.00")
        explanation = (
            f"Publicación reciente ({days_on_market} días): "
            f"el vendedor no tiene urgencia inmediata."
        )
    elif days_on_market <= 20:
        score = Decimal("70.00")
        explanation = f"Tiempo habitual en mercado ({days_on_market} días)."
    elif days_on_market <= 45:
        score = Decimal("85.00")
        explanation = f"Tiempo maduro para negociación ({days_on_market} días en mercado)."
    else:
        if seller_pressure_level == SellerPressureLevel.HIGH:
            score = Decimal("100.00")
            explanation = (
                f"Máxima oportunidad de negociación: {days_on_market} días publicado "
                f"y alta presión del vendedor."
            )
            flags.append("HIGH_NEGOTIATION_POWER")
        else:
            score = Decimal("60.00")
            explanation = f"Anuncio prolongado ({days_on_market} días) pero sin rebajas activas."

    return _quantize_score(score), explanation, flags


def evaluate_opportunity_score(
    weights: dict[str, float] | None,
    asking_price: Decimal,
    market_median: Decimal | None,
    market_low: Decimal | None,
    market_high: Decimal | None,
    classification_status: str | None,
    brand: str,
    model: str,
    fuel_type: str | None,
    known_issues_count: int,
    has_recall_campaign: bool,
    max_severity: str | None,
    repair_cost_max: Decimal,
    mitigations_count: int,
    mileage_km: int | None,
    year: int | None,
    snapshots_count: int,
    price_reductions: int,
    price_increases: int,
    title: str | None,
    description: str | None,
    days_on_market: int,
    seller_pressure_level: SellerPressureLevel,
) -> dict[str, Any]:
    """Evalúa de forma puramente determinista los 9 componentes del Opportunity Score."""
    resolved_weights = weights or DEFAULT_SCORING_WEIGHTS

    price_s, price_exp, price_flags = compute_price_score(
        asking_price, market_median, market_low, market_high
    )
    rel_s, rel_exp, rel_flags = compute_reliability_score(classification_status)
    liq_s, liq_exp, liq_flags = compute_liquidity_score(brand, model, fuel_type)
    mech_s, mech_exp, mech_flags = compute_mechanical_risk_score(
        known_issues_count,
        has_recall_campaign,
        max_severity,
        repair_cost_max,
        mitigations_count,
    )
    mil_s, mil_exp, mil_flags = compute_mileage_score(mileage_km, year, fuel_type)
    age_s, age_exp, age_flags = compute_age_score(year)
    hist_s, hist_exp, hist_flags = compute_history_score(
        snapshots_count, price_reductions, price_increases
    )
    cond_s, cond_exp, cond_flags = compute_condition_score(title, description)
    lage_s, lage_exp, lage_flags = compute_listing_age_score(days_on_market, seller_pressure_level)

    scores_map = {
        ScoringComponent.PRICE.value: (price_s, price_exp, price_flags),
        ScoringComponent.RELIABILITY.value: (rel_s, rel_exp, rel_flags),
        ScoringComponent.LIQUIDITY.value: (liq_s, liq_exp, liq_flags),
        ScoringComponent.MECHANICAL_RISK.value: (mech_s, mech_exp, mech_flags),
        ScoringComponent.MILEAGE.value: (mil_s, mil_exp, mil_flags),
        ScoringComponent.AGE.value: (age_s, age_exp, age_flags),
        ScoringComponent.HISTORY.value: (hist_s, hist_exp, hist_flags),
        ScoringComponent.CONDITION.value: (cond_s, cond_exp, cond_flags),
        ScoringComponent.LISTING_AGE.value: (lage_s, lage_exp, lage_flags),
    }

    breakdown: dict[str, Any] = {}
    total_score = Decimal("0.00")

    for comp_name, (score_val, exp, flags) in scores_map.items():
        w = Decimal(str(resolved_weights.get(comp_name, 0.0)))
        weighted = (score_val * w).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_score += weighted
        breakdown[comp_name] = {
            "component": comp_name,
            "score": float(score_val),
            "weight": float(w),
            "weighted_score": float(weighted),
            "explanation": exp,
            "flags": flags,
        }

    total_clamped = _quantize_score(total_score)

    return {
        "total_score": total_clamped,
        "price_score": price_s,
        "reliability_score": rel_s,
        "liquidity_score": liq_s,
        "mechanical_risk_score": mech_s,
        "mileage_score": mil_s,
        "age_score": age_s,
        "history_score": hist_s,
        "condition_score": cond_s,
        "listing_age_score": lage_s,
        "score_breakdown": breakdown,
    }
