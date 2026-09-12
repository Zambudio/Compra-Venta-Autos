"""Alembic model registry.

Importing this module registers every ORM model on the shared metadata.
"""

from app.audit.models import AuditEvent
from app.auth.models import AuthSession
from app.files.models import FileAttachment
from app.inspections.models import Inspection, InspectionCheck
from app.knowledge.models import (
    Engine,
    EngineVariant,
    Evidence,
    KnowledgeSource,
    KnownIssue,
    Manufacturer,
    TransmissionSpec,
    VehicleClassification,
    VehicleGeneration,
    VehicleMitigation,
    VehicleModel,
)
from app.listings.models import ListingSnapshot, RawListingPayload, VehicleListing
from app.scoring.models import (
    Opportunity,
    OpportunityScore,
    ScoringProfile,
    ScoringProfileVersion,
)
from app.sources.models import Source, SourceComplianceReview, SourceSyncRun
from app.users.models import User
from app.vehicles.models import MarketEstimate, Vehicle, VehicleMatchCandidate
from app.watchlist.models import WatchlistEntry

__all__ = [
    "AuditEvent",
    "AuthSession",
    "Engine",
    "EngineVariant",
    "Evidence",
    "FileAttachment",
    "Inspection",
    "InspectionCheck",
    "KnowledgeSource",
    "KnownIssue",
    "ListingSnapshot",
    "Manufacturer",
    "MarketEstimate",
    "Opportunity",
    "OpportunityScore",
    "RawListingPayload",
    "ScoringProfile",
    "ScoringProfileVersion",
    "Source",
    "SourceComplianceReview",
    "SourceSyncRun",
    "TransmissionSpec",
    "User",
    "Vehicle",
    "VehicleClassification",
    "VehicleGeneration",
    "VehicleListing",
    "VehicleMatchCandidate",
    "VehicleMitigation",
    "VehicleModel",
    "WatchlistEntry",
]
