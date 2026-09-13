"""DTOs de la API de anuncios. Nunca exponen `payload` crudo ni `payload_hash`."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.connectors.filters import ConnectorSearchFilter
from app.listings.vocab import FuelType, ListingStatus, SellerType, Transmission


class SnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    observed_at: datetime
    price_amount: Decimal
    price_currency: str
    mileage_km: int
    status: ListingStatus


class ListingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_key: str
    external_id: str
    url: str | None
    brand: str
    model: str
    generation: str | None
    trim: str | None
    engine_code: str | None
    power_kw: int | None
    fuel_type: FuelType
    transmission: Transmission
    year: int
    mileage_km: int
    price_amount: Decimal
    price_currency: str
    location: str | None
    province: str | None
    seller_type: SellerType
    description: str | None
    image_urls: list[str]
    status: ListingStatus
    first_seen_at: datetime
    last_seen_at: datetime
    published_at: datetime | None


class ListingDetailRead(ListingRead):
    snapshots: list[SnapshotRead]


class ListingPage(BaseModel):
    items: list[ListingRead]
    page: int
    page_size: int
    total: int
    has_more: bool


class LiveSearchFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=2, max_length=120)
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    location: str | None = Field(default=None, max_length=120)
    category: str | None = Field(default=None, max_length=80)
    source: Literal["wallapop"] = "wallapop"
    limit: int = Field(default=20, ge=1, le=50)
    offset: int = Field(default=0, ge=0, le=10_000)

    @field_validator("query", "location", "category", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_price_range(self) -> LiveSearchFilters:
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            raise ValueError("min_price must not exceed max_price")
        return self

    def to_connector_filter(self) -> ConnectorSearchFilter:
        return ConnectorSearchFilter(
            query=self.query,
            price_min=self.min_price,
            price_max=self.max_price,
            location=self.location,
            category=self.category,
            page=self.offset // self.limit + 1,
            page_size=self.limit,
            offset=self.offset,
        )


class WallapopListing(BaseModel):
    id: str
    title: str
    description: str
    price: Decimal = Field(ge=0)
    location: str | None
    images: list[str]
    seller: dict[str, Any]
    url: str
    posted_at: datetime | None
    source_key: Literal["wallapop"] = "wallapop"


class LiveSearchResult(BaseModel):
    total: int = Field(ge=0)
    listings: list[WallapopListing]
    query: str
    filters: dict[str, Any]


class ManualListingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str | None = Field(default=None, max_length=2048)
    brand: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=120)
    trim: str | None = Field(default=None, max_length=160)
    generation: str | None = Field(default=None, max_length=120)
    engine_code: str | None = Field(default=None, max_length=40)
    year: int = Field(ge=1950, le=2100)
    mileage_km: int = Field(ge=0, le=2_000_000)
    price_amount: Decimal = Field(gt=0, le=Decimal("1000000"))
    fuel_type: FuelType = FuelType.OTHER
    transmission: Transmission = Transmission.UNKNOWN
    seller_type: SellerType = SellerType.UNKNOWN
    province: str | None = Field(default=None, max_length=80)
    location: str | None = Field(default=None, max_length=160)
    description: str | None = Field(default=None, max_length=5000)
    image_urls: list[str] = Field(default_factory=list, max_length=20)
