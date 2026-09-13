"""DTOs de la API de fuentes. Nunca exponen payloads crudos ni hashes."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.connectors.filters import ConnectorSearchFilter
from app.listings.vocab import FuelType, ProviderKind, SellerType, SyncRunStatus


class ComplianceReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    acquisition_method: str
    automated_allowed: bool
    authentication_required: str
    rate_limit: str | None
    terms_url: str | None
    checked_at: datetime
    notes: str


class SourceUpdate(BaseModel):
    is_active: bool | None = None


class SourceConfigUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool | None = None
    config: dict[str, Any] | None = None

    @model_validator(mode="after")
    def require_a_change(self) -> SourceConfigUpdate:
        if self.enabled is None and self.config is None:
            raise ValueError("enabled or config is required")
        return self


class SourceConfigRead(BaseModel):
    key: str
    enabled: bool
    config: dict[str, Any]
    last_sync: datetime | None
    sync_error: str | None
    updated_at: datetime

class SourceRead(BaseModel):
    key: str
    name: str
    provider_kind: ProviderKind
    is_active: bool
    is_automatable: bool
    latest_review: ComplianceReviewRead | None
    enabled: bool | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    last_sync: datetime | None = None
    sync_error: str | None = None
    health: str | None = None


class SourceHealthRead(BaseModel):
    source_key: str
    healthy: bool
    detail: str
    checked_at: datetime


class SyncRunRead(BaseModel):
    id: UUID
    source_key: str
    status: SyncRunStatus
    mode: str
    listings_seen: int
    listings_created: int
    listings_updated: int
    snapshots_created: int
    error_summary: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class SyncMode(StrEnum):
    SYNC = "sync"
    ASYNC = "async"


class SyncRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brand: str | None = None
    model: str | None = None
    year_min: int | None = Field(default=None, ge=1950, le=2100)
    year_max: int | None = Field(default=None, ge=1950, le=2100)
    price_min: Decimal | None = Field(default=None, ge=0)
    price_max: Decimal | None = Field(default=None, ge=0)
    fuel_type: FuelType | None = None
    mileage_max: int | None = Field(default=None, ge=0)
    province: str | None = None
    seller_type: SellerType | None = None

    def as_filter_dict(self) -> dict[str, object]:
        return self.model_dump(mode="json", exclude_none=True)

    def to_connector_filter(self, *, page: int, page_size: int) -> ConnectorSearchFilter:
        return ConnectorSearchFilter(
            brand=self.brand,
            model=self.model,
            year_min=self.year_min,
            year_max=self.year_max,
            price_min=self.price_min,
            price_max=self.price_max,
            fuel_type=self.fuel_type,
            mileage_max=self.mileage_max,
            province=self.province,
            seller_type=self.seller_type,
            page=page,
            page_size=page_size,
        )
