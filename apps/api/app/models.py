"""Alembic model registry.

Importing this module registers every ORM model on the shared metadata.
"""

from app.audit.models import AuditEvent
from app.auth.models import AuthSession
from app.listings.models import ListingSnapshot, RawListingPayload, VehicleListing
from app.sources.models import Source, SourceComplianceReview, SourceSyncRun
from app.users.models import User
from app.vehicles.models import MarketEstimate, Vehicle, VehicleMatchCandidate

__all__ = [
    "AuditEvent",
    "AuthSession",
    "ListingSnapshot",
    "MarketEstimate",
    "RawListingPayload",
    "Source",
    "SourceComplianceReview",
    "SourceSyncRun",
    "User",
    "Vehicle",
    "VehicleListing",
    "VehicleMatchCandidate",
]
