"""Esquemas Pydantic / DTOs para el dominio Knowledge Base."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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

# --- Jerarquía Técnica ---


class ManufacturerBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    country: str | None = Field(default=None, max_length=60)


class ManufacturerCreate(ManufacturerBase):
    pass


class ManufacturerRead(ManufacturerBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class VehicleModelBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class VehicleModelCreate(VehicleModelBase):
    manufacturer_id: UUID


class VehicleModelRead(VehicleModelBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    manufacturer_id: UUID
    created_at: datetime
    updated_at: datetime


class VehicleGenerationBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    year_start: int = Field(ge=1900, le=2100)
    year_end: int | None = Field(default=None, ge=1900, le=2100)


class VehicleGenerationCreate(VehicleGenerationBase):
    model_id: UUID


class VehicleGenerationRead(VehicleGenerationBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    model_id: UUID
    created_at: datetime
    updated_at: datetime


class EngineBase(BaseModel):
    family_code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=120)
    displacement_cc: int | None = Field(default=None, ge=100, le=12000)
    fuel_type: FuelType
    aspiration: EngineAspiration = EngineAspiration.NATURALLY_ASPIRATED


class EngineCreate(EngineBase):
    manufacturer_id: UUID


class EngineRead(EngineBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    manufacturer_id: UUID
    created_at: datetime
    updated_at: datetime


class EngineVariantBase(BaseModel):
    version_code: str | None = Field(default=None, max_length=60)
    power_kw: int | None = Field(default=None, ge=10, le=2000)
    power_cv: int | None = Field(default=None, ge=10, le=3000)
    torque_nm: int | None = Field(default=None, ge=20, le=3000)
    year_start: int | None = Field(default=None, ge=1900, le=2100)
    year_end: int | None = Field(default=None, ge=1900, le=2100)


class EngineVariantCreate(EngineVariantBase):
    engine_id: UUID


class EngineVariantRead(EngineVariantBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    engine_id: UUID
    created_at: datetime
    updated_at: datetime


class TransmissionSpecBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    code: str | None = Field(default=None, max_length=60)
    type: TransmissionType = TransmissionType.MANUAL
    gears: int | None = Field(default=None, ge=1, le=12)


class TransmissionSpecCreate(TransmissionSpecBase):
    manufacturer_id: UUID | None = None


class TransmissionSpecRead(TransmissionSpecBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    manufacturer_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


# --- Fuentes y Evidencias ---


class KnowledgeSourceBase(BaseModel):
    source_type: KnowledgeSourceType
    name: str = Field(min_length=1, max_length=200)
    url: str | None = Field(default=None, max_length=2048)
    publisher: str | None = Field(default=None, max_length=150)
    published_at: datetime | None = None
    trust_level: SourceTrustLevel
    notes: str | None = None


class KnowledgeSourceCreate(KnowledgeSourceBase):
    pass


class KnowledgeSourceRead(KnowledgeSourceBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    retrieved_at: datetime
    created_at: datetime
    updated_at: datetime


class KnowledgeSourcePage(BaseModel):
    items: list[KnowledgeSourceRead]
    page: int
    page_size: int
    total: int
    has_more: bool


class EvidenceBase(BaseModel):
    component: VehicleComponent
    summary: str = Field(min_length=1, max_length=2000)
    severity: IssueSeverity
    confidence_score: Decimal = Field(ge=Decimal("0.0"), le=Decimal("1.0"))
    verified: bool = False


class EvidenceCreate(EvidenceBase):
    source_id: UUID


class EvidenceRead(EvidenceBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    source_id: UUID
    verified_by_user_id: UUID | None = None
    verified_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    source: KnowledgeSourceRead | None = None


class EvidencePage(BaseModel):
    items: list[EvidenceRead]
    page: int
    page_size: int
    total: int
    has_more: bool


# --- Problemas Conocidos ---


class KnownIssueBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str
    component: VehicleComponent
    severity: IssueSeverity
    frequency: IssueFrequency
    typical_mileage_km: int | None = Field(default=None, ge=0)
    estimated_repair_cost_min: Decimal = Field(ge=Decimal("0.0"))
    estimated_repair_cost_max: Decimal = Field(ge=Decimal("0.0"))
    currency: str = "EUR"
    symptoms: str | None = None
    prevention: str | None = None
    definitive_repair: str | None = None
    has_recall_campaign: bool = False
    recall_details: str | None = None
    status: IssueStatus = IssueStatus.DRAFT


class KnownIssueCreate(KnownIssueBase):
    evidence_ids: list[UUID] = Field(default_factory=list)
    engine_ids: list[UUID] = Field(default_factory=list)
    engine_variant_ids: list[UUID] = Field(default_factory=list)
    generation_ids: list[UUID] = Field(default_factory=list)
    transmission_ids: list[UUID] = Field(default_factory=list)


class KnownIssueUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    component: VehicleComponent | None = None
    severity: IssueSeverity | None = None
    frequency: IssueFrequency | None = None
    typical_mileage_km: int | None = None
    estimated_repair_cost_min: Decimal | None = None
    estimated_repair_cost_max: Decimal | None = None
    symptoms: str | None = None
    prevention: str | None = None
    definitive_repair: str | None = None
    has_recall_campaign: bool | None = None
    recall_details: str | None = None
    status: IssueStatus | None = None
    evidence_ids: list[UUID] | None = None
    engine_ids: list[UUID] | None = None
    engine_variant_ids: list[UUID] | None = None
    generation_ids: list[UUID] | None = None
    transmission_ids: list[UUID] | None = None


class KnownIssueRead(KnownIssueBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    reviewed_by_user_id: UUID | None = None
    reviewed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class KnownIssueDetailRead(KnownIssueRead):
    evidences: list[EvidenceRead] = Field(default_factory=list)
    engines: list[EngineRead] = Field(default_factory=list)
    engine_variants: list[EngineVariantRead] = Field(default_factory=list)
    generations: list[VehicleGenerationRead] = Field(default_factory=list)
    transmissions: list[TransmissionSpecRead] = Field(default_factory=list)


class KnownIssuePage(BaseModel):
    items: list[KnownIssueRead]
    page: int
    page_size: int
    total: int
    has_more: bool


# --- Clasificaciones de Fiabilidad ---


class VehicleClassificationBase(BaseModel):
    target_type: ClassificationTargetType
    target_id: UUID
    status: ClassificationStatus
    rationale: str
    validity_start: datetime | None = None
    validity_end: datetime | None = None


class VehicleClassificationCreate(VehicleClassificationBase):
    pass


class VehicleClassificationRead(VehicleClassificationBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class VehicleClassificationPage(BaseModel):
    items: list[VehicleClassificationRead]
    page: int
    page_size: int
    total: int
    has_more: bool


# --- Diagnóstico / Lookup de Fiabilidad ---


class ReliabilityLookupResponse(BaseModel):
    brand: str
    model: str
    year: int | None = None
    fuel_type: str | None = None
    engine_code: str | None = None
    classification: ClassificationStatus = ClassificationStatus.UNKNOWN
    classification_rationale: str | None = None
    issues_count: int
    max_severity: IssueSeverity | None = None
    total_estimated_repair_min: Decimal = Decimal("0.0")
    total_estimated_repair_max: Decimal = Decimal("0.0")
    currency: str = "EUR"
    has_recalls: bool = False
    issues: list[KnownIssueRead] = Field(default_factory=list)
    preventive_recommendations: list[str] = Field(default_factory=list)


# --- Mitigaciones en Vehículos Concretos ---


class VehicleMitigationBase(BaseModel):
    mitigation_type: str = Field(min_length=1, max_length=80)
    description: str
    applied_at: datetime | None = None


class VehicleMitigationCreate(VehicleMitigationBase):
    vehicle_id: UUID
    known_issue_id: UUID


class VehicleMitigationRead(VehicleMitigationBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    vehicle_id: UUID
    known_issue_id: UUID
    verified_by_user_id: UUID | None = None
    created_at: datetime
    known_issue: KnownIssueRead | None = None
