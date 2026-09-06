"""Modelos de fuentes de adquisición y su trazabilidad de cumplimiento.

`Source` es el catálogo de portales/importadores; `SourceComplianceReview` es un
historial append-only de las revisiones de cumplimiento (Plan Maestro §9);
`SourceSyncRun` registra cada ejecución de sincronización para observabilidad e
idempotencia del actor Dramatiq (§39/§41, ADR-0004, ADR-0012).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.models import Base, TimestampMixin
from app.listings.vocab import ProviderKind, SyncRunStatus

_provider_kind = Enum(ProviderKind, name="provider_kind", native_enum=False, create_constraint=True)
_sync_run_status = Enum(
    SyncRunStatus, name="sync_run_status", native_enum=False, create_constraint=True
)


class Source(TimestampMixin, Base):
    __tablename__ = "sources"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    key: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    provider_kind: Mapped[ProviderKind] = mapped_column(_provider_kind, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_automatable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    compliance_reviews: Mapped[list[SourceComplianceReview]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )
    sync_runs: Mapped[list[SourceSyncRun]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class SourceComplianceReview(Base):
    __tablename__ = "source_compliance_reviews"
    __table_args__ = (
        Index("ix_source_compliance_reviews_source_checked", "source_id", "checked_at"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    acquisition_method: Mapped[str] = mapped_column(String(120), nullable=False)
    automated_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    authentication_required: Mapped[str] = mapped_column(String(120), nullable=False)
    rate_limit: Mapped[str | None] = mapped_column(String(120), nullable=True)
    terms_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    source: Mapped[Source] = relationship(back_populates="compliance_reviews")


class SourceSyncRun(Base):
    __tablename__ = "source_sync_runs"
    __table_args__ = (Index("ix_source_sync_runs_source_created", "source_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[SyncRunStatus] = mapped_column(
        _sync_run_status, nullable=False, default=SyncRunStatus.PENDING
    )
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    filters: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    job_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    listings_seen: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    listings_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    listings_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    snapshots_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    source: Mapped[Source] = relationship(back_populates="sync_runs")
