"""Alembic model registry.

Importing this module registers every ORM model on the shared metadata.
"""

from app.audit.models import AuditEvent
from app.auth.models import AuthSession
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
from app.sources.models import Source, SourceComplianceReview, SourceSyncRun
from app.users.models import User
from app.vehicles.models import MarketEstimate, Vehicle, VehicleMatchCandidate

__all__ = [
    "AuditEvent",
    "AuthSession",
    "Engine",
    "EngineVariant",
    "Evidence",
    "KnowledgeSource",
    "KnownIssue",
    "ListingSnapshot",
    "Manufacturer",
    "MarketEstimate",
    "RawListingPayload",
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
]
