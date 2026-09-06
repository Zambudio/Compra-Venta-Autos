"""Alembic model registry.

Importing this module registers every ORM model on the shared metadata.
"""

from app.audit.models import AuditEvent
from app.auth.models import AuthSession
from app.users.models import User

__all__ = ["AuditEvent", "AuthSession", "User"]
