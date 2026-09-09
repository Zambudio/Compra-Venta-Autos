"""Modelos SQLAlchemy para perfiles de scoring, puntuaciones inmutables y oportunidades (Fase 5)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
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
from app.listings.models import VehicleListing
from app.scoring.vocab import ConfidenceLevel, OpportunityStatus, SellerPressureLevel
from app.vehicles.models import Vehicle

_opportunity_status = Enum(
    OpportunityStatus,
    name="opportunity_status",
    native_enum=False,
    create_constraint=True,
)
_confidence_level = Enum(
    ConfidenceLevel,
    name="confidence_level",
    native_enum=False,
    create_constraint=True,
)
_seller_pressure_level = Enum(
    SellerPressureLevel,
    name="seller_pressure_level",
    native_enum=False,
    create_constraint=True,
)


class ScoringProfile(TimestampMixin, Base):
    __tablename__ = "scoring_profiles"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    versions: Mapped[list[ScoringProfileVersion]] = relationship(
        "ScoringProfileVersion",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="desc(ScoringProfileVersion.version_number)",
    )


class ScoringProfileVersion(TimestampMixin, Base):
    __tablename__ = "scoring_profile_versions"
    __table_args__ = (
        UniqueConstraint("profile_id", "version_number", name="uq_profile_version"),
        Index("ix_scoring_profile_versions_profile_id", "profile_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("scoring_profiles.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    weights: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    is_immutable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    profile: Mapped[ScoringProfile] = relationship("ScoringProfile", back_populates="versions")
    scores: Mapped[list[OpportunityScore]] = relationship(
        "OpportunityScore", back_populates="profile_version"
    )


class OpportunityScore(Base):
    __tablename__ = "opportunity_scores"
    __table_args__ = (
        CheckConstraint(
            "(vehicle_id IS NOT NULL) OR (listing_id IS NOT NULL)",
            name="score_target_present",
        ),
        Index("ix_opportunity_scores_total", "total_score"),
        Index("ix_opportunity_scores_calc_at", "calculated_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    vehicle_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=True, index=True
    )
    listing_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("vehicle_listings.id", ondelete="CASCADE"), nullable=True, index=True
    )
    profile_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("scoring_profile_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    total_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    price_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    reliability_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    liquidity_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    mechanical_risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    mileage_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    age_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    history_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    condition_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    listing_age_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    score_breakdown: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    profile_version: Mapped[ScoringProfileVersion] = relationship(
        "ScoringProfileVersion", back_populates="scores"
    )
    vehicle: Mapped[Vehicle | None] = relationship("Vehicle")
    listing: Mapped[VehicleListing | None] = relationship("VehicleListing")


class Opportunity(TimestampMixin, Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        CheckConstraint(
            "(vehicle_id IS NOT NULL) OR (listing_id IS NOT NULL)",
            name="opportunity_target_present",
        ),
        Index("ix_opportunities_status", "status"),
        Index("ix_opportunities_created", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    vehicle_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=True, index=True
    )
    listing_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("vehicle_listings.id", ondelete="CASCADE"), nullable=True, index=True
    )
    score_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("opportunity_scores.id", ondelete="SET NULL"), nullable=True, index=True
    )

    status: Mapped[OpportunityStatus] = mapped_column(
        _opportunity_status, nullable=False, default=OpportunityStatus.IDENTIFIED
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")

    asking_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    estimated_market_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    estimated_fast_sale_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    target_purchase_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    estimated_transfer_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    estimated_tax: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    estimated_repair_min: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    estimated_repair_max: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    estimated_preparation_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("200.00")
    )

    estimated_total_cost_min: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    estimated_total_cost_max: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    estimated_margin_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    estimated_margin_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    estimated_roi_min: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    estimated_roi_max: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)

    confidence_level: Mapped[ConfidenceLevel] = mapped_column(
        _confidence_level, nullable=False, default=ConfidenceLevel.LOW
    )
    seller_pressure_level: Mapped[SellerPressureLevel] = mapped_column(
        _seller_pressure_level, nullable=False, default=SellerPressureLevel.LOW
    )
    seller_pressure_reasons: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    vehicle: Mapped[Vehicle | None] = relationship("Vehicle")
    listing: Mapped[VehicleListing | None] = relationship("VehicleListing")
    score: Mapped[OpportunityScore | None] = relationship("OpportunityScore")
