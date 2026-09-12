from __future__ import annotations

from uuid import UUID, uuid4

from app.core.models import Base, TimestampMixin
from app.scoring.models import Opportunity
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class WatchlistEntry(TimestampMixin, Base):
    __tablename__ = "watchlist_entries"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    opportunity_id: Mapped[UUID] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    opportunity: Mapped[Opportunity] = relationship("Opportunity")
