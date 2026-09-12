from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from app.core.models import Base, TimestampMixin
from app.knowledge.models import KnownIssue
from app.watchlist.models import WatchlistEntry
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .vocab import CheckResult, InspectionStatus

_inspection_status = Enum(
    InspectionStatus,
    name="inspection_status",
    native_enum=False,
    create_constraint=True,
)

_check_result = Enum(
    CheckResult,
    name="check_result",
    native_enum=False,
    create_constraint=True,
)


class Inspection(TimestampMixin, Base):
    __tablename__ = "inspections"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    watchlist_entry_id: Mapped[UUID] = mapped_column(
        ForeignKey("watchlist_entries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[InspectionStatus] = mapped_column(
        _inspection_status, nullable=False, default=InspectionStatus.DRAFT
    )
    inspector_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    watchlist_entry: Mapped[WatchlistEntry] = relationship("WatchlistEntry")
    checks: Mapped[list[InspectionCheck]] = relationship(
        "InspectionCheck", back_populates="inspection", cascade="all, delete-orphan"
    )


class InspectionCheck(TimestampMixin, Base):
    __tablename__ = "inspection_checks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    inspection_id: Mapped[UUID] = mapped_column(
        ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    known_issue_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("known_issues.id", ondelete="SET NULL"), nullable=True
    )
    result: Mapped[CheckResult] = mapped_column(
        _check_result, nullable=False, default=CheckResult.NOT_CHECKED
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    inspection: Mapped[Inspection] = relationship("Inspection", back_populates="checks")
    known_issue: Mapped[KnownIssue | None] = relationship("KnownIssue")
