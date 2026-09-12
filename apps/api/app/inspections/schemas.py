from datetime import datetime
from uuid import UUID

from app.inspections.vocab import CheckResult, InspectionStatus
from pydantic import BaseModel, ConfigDict


class InspectionCheckBase(BaseModel):
    category: str
    name: str
    description: str | None = None
    known_issue_id: UUID | None = None
    result: CheckResult = CheckResult.NOT_CHECKED
    notes: str | None = None


class InspectionCheckCreate(InspectionCheckBase):
    pass


class InspectionCheckUpdate(BaseModel):
    result: CheckResult | None = None
    notes: str | None = None
    known_issue_id: UUID | None = None


class InspectionCheckPublic(InspectionCheckBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    inspection_id: UUID
    created_at: datetime
    updated_at: datetime


class InspectionBase(BaseModel):
    watchlist_entry_id: UUID
    status: InspectionStatus = InspectionStatus.DRAFT
    inspector_name: str | None = None
    scheduled_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = None


class InspectionCreate(BaseModel):
    watchlist_entry_id: UUID
    inspector_name: str | None = None
    scheduled_at: datetime | None = None
    notes: str | None = None


class InspectionUpdate(BaseModel):
    status: InspectionStatus | None = None
    inspector_name: str | None = None
    scheduled_at: datetime | None = None
    notes: str | None = None


class InspectionPublic(InspectionBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class InspectionWithDetails(InspectionPublic):
    checks: list[InspectionCheckPublic]
