"""Esquemas Pydantic / DTOs para el dominio de vehículos y matching."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.listings.vocab import FuelType, ListingStatus, Transmission
from app.vehicles.vocab import MarketEstimateMethod, MatchCandidateStatus


class VehicleListingSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID
    external_id: str
    brand: str
    model: str
    year: int
    mileage_km: int
    price_amount: Decimal
    price_currency: str
    province: str | None = None
    status: ListingStatus
    image_urls: list[str] = Field(default_factory=list)


class MatchCandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    listing_a_id: UUID
    listing_b_id: UUID
    confidence_score: Decimal
    match_reasons: dict[str, Any]
    status: MatchCandidateStatus
    decided_by_user_id: UUID | None = None
    decided_at: datetime | None = None
    created_at: datetime
    listing_a: VehicleListingSummary | None = None
    listing_b: VehicleListingSummary | None = None


class MatchCandidatePage(BaseModel):
    items: list[MatchCandidateRead]
    page: int
    page_size: int
    total: int
    has_more: bool


class ConfirmMatchResponse(BaseModel):
    candidate_id: UUID
    status: MatchCandidateStatus
    vehicle_id: UUID


class RejectMatchResponse(BaseModel):
    candidate_id: UUID
    status: MatchCandidateStatus


class VehicleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brand: str
    model: str
    generation: str | None = None
    trim: str | None = None
    engine_code: str | None = None
    power_kw: int | None = None
    fuel_type: FuelType
    transmission: Transmission
    year: int
    first_listed_at: datetime
    listing_count: int
    created_at: datetime
    updated_at: datetime


class VehiclePage(BaseModel):
    items: list[VehicleRead]
    page: int
    page_size: int
    total: int
    has_more: bool


class MarketEstimateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vehicle_id: UUID | None = None
    listing_id: UUID | None = None
    estimated_amount: Decimal
    low_amount: Decimal
    high_amount: Decimal
    currency: str = "EUR"
    method: MarketEstimateMethod
    number_of_comparables: int
    confidence_score: Decimal
    calculated_at: datetime


class ListingHistoryMetrics(BaseModel):
    initial_price: Decimal
    current_price: Decimal
    price_delta: Decimal
    price_delta_percentage: Decimal
    days_on_market: int
    number_of_price_changes: int
    is_relisted: bool


class VehicleHistoryMetrics(BaseModel):
    lowest_observed_price: Decimal
    highest_observed_price: Decimal
    current_min_price: Decimal
    days_on_market: int
    total_price_changes: int


class VehicleDetailRead(VehicleRead):
    listings: list[VehicleListingSummary] = Field(default_factory=list)
    history: VehicleHistoryMetrics | None = None
    market_estimate: MarketEstimateRead | None = None
