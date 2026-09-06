"""Modelos SQLAlchemy para vehículos, candidatos de deduplicación y estimaciones de mercado."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.models import Base, TimestampMixin
from app.listings.vocab import FuelType, Transmission
from app.vehicles.vocab import MarketEstimateMethod, MatchCandidateStatus

if TYPE_CHECKING:
    from app.listings.models import VehicleListing
    from app.users.models import User

_fuel_type = Enum(FuelType, name="fuel_type", native_enum=False, create_constraint=True)
_transmission = Enum(Transmission, name="transmission", native_enum=False, create_constraint=True)
_match_candidate_status = Enum(
    MatchCandidateStatus,
    name="match_candidate_status",
    native_enum=False,
    create_constraint=True,
)
_estimate_method = Enum(
    MarketEstimateMethod,
    name="market_estimate_method",
    native_enum=False,
    create_constraint=True,
)


class Vehicle(TimestampMixin, Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        Index("ix_vehicles_brand_model", "brand", "model"),
        Index("ix_vehicles_year", "year"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    brand: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    generation: Mapped[str | None] = mapped_column(String(120), nullable=True)
    trim: Mapped[str | None] = mapped_column(String(160), nullable=True)
    engine_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    power_kw: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fuel_type: Mapped[FuelType] = mapped_column(_fuel_type, nullable=False)
    transmission: Mapped[Transmission] = mapped_column(_transmission, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    first_listed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    listing_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    listings: Mapped[list[VehicleListing]] = relationship(
        "VehicleListing", back_populates="vehicle"
    )
    estimates: Mapped[list[MarketEstimate]] = relationship(
        "MarketEstimate", back_populates="vehicle", cascade="all, delete-orphan"
    )


class VehicleMatchCandidate(TimestampMixin, Base):
    __tablename__ = "vehicle_match_candidates"
    __table_args__ = (
        CheckConstraint("listing_a_id < listing_b_id", name="pair_order"),
        UniqueConstraint("listing_a_id", "listing_b_id", name="uq_match_candidate_pair"),
        Index("ix_match_candidates_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    listing_a_id: Mapped[UUID] = mapped_column(
        ForeignKey("vehicle_listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    listing_b_id: Mapped[UUID] = mapped_column(
        ForeignKey("vehicle_listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    match_reasons: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[MatchCandidateStatus] = mapped_column(
        _match_candidate_status, nullable=False, default=MatchCandidateStatus.PENDING
    )
    decided_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    listing_a: Mapped[VehicleListing] = relationship("VehicleListing", foreign_keys=[listing_a_id])
    listing_b: Mapped[VehicleListing] = relationship("VehicleListing", foreign_keys=[listing_b_id])
    decided_by_user: Mapped[User | None] = relationship("User", foreign_keys=[decided_by_user_id])


class MarketEstimate(Base):
    __tablename__ = "market_estimates"
    __table_args__ = (
        CheckConstraint(
            "(vehicle_id IS NOT NULL) OR (listing_id IS NOT NULL)",
            name="target_present",
        ),
        Index("ix_market_estimates_calculated_at", "calculated_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    vehicle_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=True, index=True
    )
    listing_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("vehicle_listings.id", ondelete="CASCADE"), nullable=True, index=True
    )
    estimated_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    low_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    high_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    method: Mapped[MarketEstimateMethod] = mapped_column(
        _estimate_method, nullable=False, default=MarketEstimateMethod.COMPARABLES_MEDIAN_IQR
    )
    number_of_comparables: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    vehicle: Mapped[Vehicle | None] = relationship("Vehicle", back_populates="estimates")
    listing: Mapped[VehicleListing | None] = relationship("VehicleListing")
