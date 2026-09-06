"""DTOs de la API de anuncios. Nunca exponen `payload` crudo ni `payload_hash`."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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
