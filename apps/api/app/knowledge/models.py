"""Modelos SQLAlchemy para la base de conocimiento técnico, evidencias y clasificaciones."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, TimestampMixin
from app.knowledge.vocab import (
    ClassificationStatus,
    ClassificationTargetType,
    EngineAspiration,
    IssueFrequency,
    IssueSeverity,
    IssueStatus,
    KnowledgeSourceType,
    SourceTrustLevel,
    TransmissionType,
    VehicleComponent,
)
from app.listings.vocab import FuelType

if TYPE_CHECKING:
    from app.vehicles.models import Vehicle

# Enums no nativos para compatibilidad SQLite / PostgreSQL
_source_trust_level = Enum(
    SourceTrustLevel, name="source_trust_level", native_enum=False, create_constraint=True
)
_knowledge_source_type = Enum(
    KnowledgeSourceType, name="knowledge_source_type", native_enum=False, create_constraint=True
)
_issue_severity = Enum(
    IssueSeverity, name="issue_severity", native_enum=False, create_constraint=True
)
_issue_frequency = Enum(
    IssueFrequency, name="issue_frequency", native_enum=False, create_constraint=True
)
_issue_status = Enum(IssueStatus, name="issue_status", native_enum=False, create_constraint=True)
_vehicle_component = Enum(
    VehicleComponent, name="vehicle_component", native_enum=False, create_constraint=True
)
_classification_status = Enum(
    ClassificationStatus, name="classification_status", native_enum=False, create_constraint=True
)
_classification_target_type = Enum(
    ClassificationTargetType,
    name="classification_target_type",
    native_enum=False,
    create_constraint=True,
)
_transmission_type = Enum(
    TransmissionType, name="transmission_type", native_enum=False, create_constraint=True
)
_engine_aspiration = Enum(
    EngineAspiration, name="engine_aspiration", native_enum=False, create_constraint=True
)
_fuel_type = Enum(FuelType, name="fuel_type", native_enum=False, create_constraint=True)


# --- Tablas intermedias Many-to-Many ---

known_issue_evidences = Table(
    "known_issue_evidences",
    Base.metadata,
    Column("known_issue_id", ForeignKey("known_issues.id", ondelete="CASCADE"), primary_key=True),
    Column("evidence_id", ForeignKey("evidences.id", ondelete="CASCADE"), primary_key=True),
)

known_issue_engines = Table(
    "known_issue_engines",
    Base.metadata,
    Column("known_issue_id", ForeignKey("known_issues.id", ondelete="CASCADE"), primary_key=True),
    Column("engine_id", ForeignKey("engines.id", ondelete="CASCADE"), primary_key=True),
)

known_issue_engine_variants = Table(
    "known_issue_engine_variants",
    Base.metadata,
    Column("known_issue_id", ForeignKey("known_issues.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "engine_variant_id", ForeignKey("engine_variants.id", ondelete="CASCADE"), primary_key=True
    ),
)

known_issue_generations = Table(
    "known_issue_generations",
    Base.metadata,
    Column("known_issue_id", ForeignKey("known_issues.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "generation_id", ForeignKey("vehicle_generations.id", ondelete="CASCADE"), primary_key=True
    ),
)

known_issue_transmissions = Table(
    "known_issue_transmissions",
    Base.metadata,
    Column("known_issue_id", ForeignKey("known_issues.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "transmission_id", ForeignKey("transmission_specs.id", ondelete="CASCADE"), primary_key=True
    ),
)


# --- Jerarquía Técnica de Catálogo ---


class Manufacturer(TimestampMixin, Base):
    """Fabricante o marca normalizada."""

    __tablename__ = "manufacturers"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    country: Mapped[str | None] = mapped_column(String(60), nullable=True)

    models: Mapped[list[VehicleModel]] = relationship(
        "VehicleModel", back_populates="manufacturer", cascade="all, delete-orphan"
    )
    engines: Mapped[list[Engine]] = relationship(
        "Engine", back_populates="manufacturer", cascade="all, delete-orphan"
    )


class VehicleModel(TimestampMixin, Base):
    """Modelo de un fabricante (ej. Golf, Ibiza, Clio, Megane)."""

    __tablename__ = "vehicle_models"
    __table_args__ = (
        UniqueConstraint("manufacturer_id", "name", name="uq_vehicle_models_manufacturer_name"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    manufacturer_id: Mapped[UUID] = mapped_column(
        ForeignKey("manufacturers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)

    manufacturer: Mapped[Manufacturer] = relationship("Manufacturer", back_populates="models")
    generations: Mapped[list[VehicleGeneration]] = relationship(
        "VehicleGeneration", back_populates="model", cascade="all, delete-orphan"
    )


class VehicleGeneration(TimestampMixin, Base):
    """Generación de un modelo acotada en años (ej. Golf IV 1997-2004, Clio IV 2012-2019)."""

    __tablename__ = "vehicle_generations"
    __table_args__ = (
        CheckConstraint("year_end IS NULL OR year_end >= year_start", name="ck_generation_years"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    model_id: Mapped[UUID] = mapped_column(
        ForeignKey("vehicle_models.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    year_start: Mapped[int] = mapped_column(Integer, nullable=False)
    year_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    model: Mapped[VehicleModel] = relationship("VehicleModel", back_populates="generations")


class Engine(TimestampMixin, Base):
    """Familia o código base de motor (ej. EB2 PureTech, EA189 TDI, K9K dCi)."""

    __tablename__ = "engines"
    __table_args__ = (
        UniqueConstraint("manufacturer_id", "family_code", name="uq_engines_manufacturer_family"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    manufacturer_id: Mapped[UUID] = mapped_column(
        ForeignKey("manufacturers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    family_code: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    displacement_cc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fuel_type: Mapped[FuelType] = mapped_column(_fuel_type, nullable=False)
    aspiration: Mapped[EngineAspiration] = mapped_column(
        _engine_aspiration, default=EngineAspiration.NATURALLY_ASPIRATED, nullable=False
    )

    manufacturer: Mapped[Manufacturer] = relationship("Manufacturer", back_populates="engines")
    variants: Mapped[list[EngineVariant]] = relationship(
        "EngineVariant", back_populates="engine", cascade="all, delete-orphan"
    )


class EngineVariant(TimestampMixin, Base):
    """Variante específica de potencia/ajuste (ej. 1.2 PureTech 110cv EB2DT, 1.9 TDI 110cv ASV)."""

    __tablename__ = "engine_variants"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    engine_id: Mapped[UUID] = mapped_column(
        ForeignKey("engines.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_code: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)
    power_kw: Mapped[int | None] = mapped_column(Integer, nullable=True)
    power_cv: Mapped[int | None] = mapped_column(Integer, nullable=True)
    torque_nm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    engine: Mapped[Engine] = relationship("Engine", back_populates="variants")


class TransmissionSpec(TimestampMixin, Base):
    """Especificación técnica de transmisión (caja de cambios)."""

    __tablename__ = "transmission_specs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    manufacturer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("manufacturers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    code: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[TransmissionType] = mapped_column(
        _transmission_type, default=TransmissionType.MANUAL, nullable=False
    )
    gears: Mapped[int | None] = mapped_column(Integer, nullable=True)


# --- Fuentes y Evidencias ---


class KnowledgeSource(TimestampMixin, Base):
    """Fuente documental trazable con nivel de confianza A-D."""

    __tablename__ = "knowledge_sources"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_type: Mapped[KnowledgeSourceType] = mapped_column(_knowledge_source_type, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(150), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    trust_level: Mapped[SourceTrustLevel] = mapped_column(
        _source_trust_level, nullable=False, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    evidences: Mapped[list[Evidence]] = relationship(
        "Evidence", back_populates="source", cascade="all, delete-orphan"
    )


class Evidence(TimestampMixin, Base):
    """Fragmento de evidencia técnica concreta asociado a una fuente."""

    __tablename__ = "evidences"
    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0.000 AND confidence_score <= 1.000", name="ck_evidence_confidence"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("knowledge_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    component: Mapped[VehicleComponent] = mapped_column(
        _vehicle_component, nullable=False, index=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[IssueSeverity] = mapped_column(_issue_severity, nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    source: Mapped[KnowledgeSource] = relationship("KnowledgeSource", back_populates="evidences")
    issues: Mapped[list[KnownIssue]] = relationship(
        "KnownIssue", secondary=known_issue_evidences, back_populates="evidences"
    )


# --- Problemas Conocidos ---


class KnownIssue(TimestampMixin, Base):
    """Problema técnico recurrente diagnosticado y documentado."""

    __tablename__ = "known_issues"
    __table_args__ = (
        CheckConstraint("estimated_repair_cost_min >= 0", name="ck_issue_cost_min"),
        CheckConstraint(
            "estimated_repair_cost_max >= estimated_repair_cost_min", name="ck_issue_cost_range"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    component: Mapped[VehicleComponent] = mapped_column(
        _vehicle_component, nullable=False, index=True
    )
    severity: Mapped[IssueSeverity] = mapped_column(_issue_severity, nullable=False, index=True)
    frequency: Mapped[IssueFrequency] = mapped_column(_issue_frequency, nullable=False)
    typical_mileage_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_repair_cost_min: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    estimated_repair_cost_max: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)
    prevention: Mapped[str | None] = mapped_column(Text, nullable=True)
    definitive_repair: Mapped[str | None] = mapped_column(Text, nullable=True)
    has_recall_campaign: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recall_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[IssueStatus] = mapped_column(
        _issue_status, default=IssueStatus.DRAFT, nullable=False, index=True
    )
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    evidences: Mapped[list[Evidence]] = relationship(
        "Evidence", secondary=known_issue_evidences, back_populates="issues"
    )
    engines: Mapped[list[Engine]] = relationship("Engine", secondary=known_issue_engines)
    engine_variants: Mapped[list[EngineVariant]] = relationship(
        "EngineVariant", secondary=known_issue_engine_variants
    )
    generations: Mapped[list[VehicleGeneration]] = relationship(
        "VehicleGeneration", secondary=known_issue_generations
    )
    transmissions: Mapped[list[TransmissionSpec]] = relationship(
        "TransmissionSpec", secondary=known_issue_transmissions
    )


# --- Clasificaciones de Fiabilidad (White / Watch / Blacklist) ---


class VehicleClassification(TimestampMixin, Base):
    """Clasificación formal basada en datos sobre un modelo, motor o transmisión."""

    __tablename__ = "vehicle_classifications"
    __table_args__ = (Index("ix_classifications_target", "target_type", "target_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    target_type: Mapped[ClassificationTargetType] = mapped_column(
        _classification_target_type, nullable=False
    )
    target_id: Mapped[UUID] = mapped_column(nullable=False)
    status: Mapped[ClassificationStatus] = mapped_column(
        _classification_status, nullable=False, index=True
    )
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    validity_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validity_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# --- Mitigaciones en Unidades Concretas ---


class VehicleMitigation(TimestampMixin, Base):
    """Mitigación o reparación preventiva acreditada en un vehículo físico individual."""

    __tablename__ = "vehicle_mitigations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    vehicle_id: Mapped[UUID] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    known_issue_id: Mapped[UUID] = mapped_column(
        ForeignKey("known_issues.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mitigation_type: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    vehicle: Mapped[Vehicle] = relationship("Vehicle")
    known_issue: Mapped[KnownIssue] = relationship("KnownIssue")
