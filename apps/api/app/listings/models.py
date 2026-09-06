"""Modelos de anuncios (Fase 2).

`VehicleListing` es la unidad persistida por `(source_id, external_id)`;
`RawListingPayload` guarda el payload original inmutable con dedup por hash;
`ListingSnapshot` es el histórico append-only de precio/km/estado (Plan Maestro
§7, §11, §12; ADR-0005, ADR-0012). La entidad `Vehicle` y la deduplicación
entre fuentes llegan en Fase 3.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.models import Base, TimestampMixin
from app.listings.vocab import EntryChannel, FuelType, ListingStatus, SellerType, Transmission

_fuel_type = Enum(FuelType, name="fuel_type", native_enum=False, create_constraint=True)
_transmission = Enum(Transmission, name="transmission", native_enum=False, create_constraint=True)
_seller_type = Enum(SellerType, name="seller_type", native_enum=False, create_constraint=True)
_listing_status = Enum(
    ListingStatus, name="listing_status", native_enum=False, create_constraint=True
)
_entry_channel = Enum(EntryChannel, name="entry_channel", native_enum=False, create_constraint=True)


class VehicleListing(TimestampMixin, Base):
    __tablename__ = "vehicle_listings"
    __table_args__ = (
        UniqueConstraint(
            "source_id", "external_id", name="uq_vehicle_listings_source_id_external_id"
        ),
        Index("ix_vehicle_listings_brand_model", "brand", "model"),
        Index("ix_vehicle_listings_price_amount", "price_amount"),
        Index("ix_vehicle_listings_year", "year"),
        Index("ix_vehicle_listings_last_seen_at", "last_seen_at"),
        Index("ix_vehicle_listings_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    brand: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    generation: Mapped[str | None] = mapped_column(String(120), nullable=True)
    trim: Mapped[str | None] = mapped_column(String(160), nullable=True)
    engine_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    power_kw: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fuel_type: Mapped[FuelType] = mapped_column(_fuel_type, nullable=False)
    transmission: Mapped[Transmission] = mapped_column(_transmission, nullable=False)

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    mileage_km: Mapped[int] = mapped_column(Integer, nullable=False)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    price_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")

    location: Mapped[str | None] = mapped_column(String(160), nullable=True)
    province: Mapped[str | None] = mapped_column(String(80), nullable=True)
    seller_type: Mapped[SellerType] = mapped_column(_seller_type, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_urls: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    status: Mapped[ListingStatus] = mapped_column(
        _listing_status, nullable=False, default=ListingStatus.ACTIVE
    )
    entry_channel: Mapped[EntryChannel] = mapped_column(_entry_channel, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    raw_payloads: Mapped[list[RawListingPayload]] = relationship(
        back_populates="listing", cascade="all, delete-orphan"
    )
    snapshots: Mapped[list[ListingSnapshot]] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
        order_by="ListingSnapshot.observed_at",
    )


class RawListingPayload(Base):
    __tablename__ = "raw_listing_payloads"
    __table_args__ = (
        UniqueConstraint(
            "source_id", "payload_hash", name="uq_raw_listing_payloads_source_id_payload_hash"
        ),
        Index("ix_raw_listing_payloads_listing_id_retrieved_at", "listing_id", "retrieved_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("vehicle_listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    connector_version: Mapped[str] = mapped_column(String(20), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    listing: Mapped[VehicleListing] = relationship(back_populates="raw_payloads")


class ListingSnapshot(Base):
    __tablename__ = "listing_snapshots"
    __table_args__ = (
        Index("ix_listing_snapshots_listing_id_observed_at", "listing_id", "observed_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("vehicle_listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    price_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    mileage_km: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ListingStatus] = mapped_column(_listing_status, nullable=False)
    description_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    listing: Mapped[VehicleListing] = relationship(back_populates="snapshots")
