"""Esquemas Pydantic para perfiles de scoring, valoraciones y oportunidades."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.scoring.vocab import (
    DEFAULT_SCORING_WEIGHTS,
    ConfidenceLevel,
    OpportunityStatus,
    ScoringComponent,
    SellerPressureLevel,
)


def _validate_weights_dict(weights: dict[str, float]) -> dict[str, float]:
    required_keys = {c.value for c in ScoringComponent}
    missing = required_keys - set(weights.keys())
    if missing:
        raise ValueError(f"Faltan componentes obligatorios en weights: {sorted(missing)}")
    total = sum(weights.values())
    if abs(total - 1.0) > 0.001:
        raise ValueError(
            f"La suma de ponderaciones debe ser 1.000 (100%), suma actual: {total:.4f}"
        )
    for k, v in weights.items():
        if v < 0.0 or v > 1.0:
            raise ValueError(
                f"El peso del componente '{k}' debe estar entre 0.0 y 1.0 (recibido: {v})"
            )
    return weights


class ScoringComponentBreakdown(BaseModel):
    component: str
    raw_value: Any
    score: Decimal
    weight: Decimal
    weighted_score: Decimal
    explanation: str
    flags: list[str] = Field(default_factory=list)


class OpportunityScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vehicle_id: UUID | None = None
    listing_id: UUID | None = None
    profile_version_id: UUID
    total_score: Decimal
    price_score: Decimal
    reliability_score: Decimal
    liquidity_score: Decimal
    mechanical_risk_score: Decimal
    mileage_score: Decimal
    age_score: Decimal
    history_score: Decimal
    condition_score: Decimal
    listing_age_score: Decimal
    score_breakdown: dict[str, Any]
    calculated_at: datetime


class ScoringProfileVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    version_number: int
    weights: dict[str, float]
    config: dict[str, Any]
    is_immutable: bool
    created_at: datetime


class ScoringProfileVersionCreate(BaseModel):
    weights: dict[str, float] = Field(default_factory=lambda: dict(DEFAULT_SCORING_WEIGHTS))
    config: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_weights(self) -> ScoringProfileVersionCreate:
        _validate_weights_dict(self.weights)
        return self


class ScoringProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    versions: list[ScoringProfileVersionRead] = Field(default_factory=list)
    active_version: ScoringProfileVersionRead | None = None


class ScoringProfileCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    initial_weights: dict[str, float] = Field(default_factory=lambda: dict(DEFAULT_SCORING_WEIGHTS))
    initial_config: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_initial_weights(self) -> ScoringProfileCreate:
        _validate_weights_dict(self.initial_weights)
        return self


class OpportunityValuationRead(BaseModel):
    asking_price: Decimal
    estimated_market_price: Decimal | None = None
    estimated_fast_sale_price: Decimal | None = None
    target_purchase_price: Decimal | None = None
    estimated_transfer_cost: Decimal
    estimated_tax: Decimal
    estimated_repair_min: Decimal
    estimated_repair_max: Decimal
    estimated_preparation_cost: Decimal
    estimated_total_cost_min: Decimal
    estimated_total_cost_max: Decimal
    estimated_margin_min: Decimal | None = None
    estimated_margin_max: Decimal | None = None
    estimated_roi_min: Decimal | None = None
    estimated_roi_max: Decimal | None = None
    confidence_level: ConfidenceLevel
    currency: str = "EUR"


class SellerPressureRead(BaseModel):
    level: SellerPressureLevel
    days_on_market: int
    price_reductions_count: int
    total_reduction_amount: Decimal
    total_reduction_percentage: Decimal
    reasons: list[str] = Field(default_factory=list)


class OpportunityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vehicle_id: UUID | None = None
    listing_id: UUID | None = None
    score_id: UUID | None = None
    status: OpportunityStatus
    currency: str = "EUR"

    asking_price: Decimal
    estimated_market_price: Decimal | None = None
    estimated_fast_sale_price: Decimal | None = None
    target_purchase_price: Decimal | None = None
    estimated_transfer_cost: Decimal
    estimated_tax: Decimal
    estimated_repair_min: Decimal
    estimated_repair_max: Decimal
    estimated_preparation_cost: Decimal
    estimated_total_cost_min: Decimal
    estimated_total_cost_max: Decimal
    estimated_margin_min: Decimal | None = None
    estimated_margin_max: Decimal | None = None
    estimated_roi_min: Decimal | None = None
    estimated_roi_max: Decimal | None = None
    confidence_level: ConfidenceLevel

    seller_pressure_level: SellerPressureLevel
    seller_pressure_reasons: list[str] = Field(default_factory=list)
    notes: str | None = None

    created_at: datetime
    updated_at: datetime

    score: OpportunityScoreRead | None = None

    # Enriquecidos para visualización ágil de tarjeta
    title: str | None = None
    brand: str | None = None
    model: str | None = None
    generation: str | None = None
    trim: str | None = None
    engine_code: str | None = None
    fuel_type: str | None = None
    transmission: str | None = None
    year: int | None = None
    mileage_km: int | None = None
    city: str | None = None
    province: str | None = None
    external_url: str | None = None
    source_name: str | None = None
    reliability_status: str | None = None
    has_recall_campaign: bool = False


class OpportunityStatusUpdate(BaseModel):
    status: OpportunityStatus
    notes: str | None = Field(default=None, max_length=2000)


class OpportunityEvaluationRequest(BaseModel):
    profile_version_id: UUID | None = None


class OpportunityPage(BaseModel):
    items: list[OpportunityRead]
    page: int
    page_size: int
    total: int
    has_more: bool
