"""Vocabulario y constantes de scoring y oportunidades (Fase 5)."""

from enum import StrEnum


class OpportunityStatus(StrEnum):
    IDENTIFIED = "IDENTIFIED"
    ANALYZING = "ANALYZING"
    VALIDATED = "VALIDATED"
    DISCARDED = "DISCARDED"


class SellerPressureLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ConfidenceLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ScoringComponent(StrEnum):
    PRICE = "price_score"
    RELIABILITY = "reliability_score"
    LIQUIDITY = "liquidity_score"
    MECHANICAL_RISK = "mechanical_risk_score"
    MILEAGE = "mileage_score"
    AGE = "age_score"
    HISTORY = "history_score"
    CONDITION = "condition_score"
    LISTING_AGE = "listing_age_score"


DEFAULT_SCORING_WEIGHTS: dict[str, float] = {
    ScoringComponent.PRICE.value: 0.25,
    ScoringComponent.RELIABILITY.value: 0.20,
    ScoringComponent.LIQUIDITY.value: 0.15,
    ScoringComponent.MECHANICAL_RISK.value: 0.15,
    ScoringComponent.MILEAGE.value: 0.08,
    ScoringComponent.AGE.value: 0.05,
    ScoringComponent.HISTORY.value: 0.05,
    ScoringComponent.CONDITION.value: 0.05,
    ScoringComponent.LISTING_AGE.value: 0.02,
}
