from datetime import datetime
from uuid import UUID

from app.scoring.schemas import OpportunityRead
from pydantic import BaseModel, ConfigDict


class WatchlistEntryBase(BaseModel):
    opportunity_id: UUID
    is_active: bool = True
    notes: str | None = None


class WatchlistEntryCreate(WatchlistEntryBase):
    pass


class WatchlistEntryUpdate(BaseModel):
    is_active: bool | None = None
    notes: str | None = None


class WatchlistEntryPublic(WatchlistEntryBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class WatchlistEntryWithOpportunity(WatchlistEntryPublic):
    opportunity: OpportunityRead
