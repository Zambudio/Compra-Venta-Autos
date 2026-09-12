from __future__ import annotations

from uuid import UUID, uuid4

from app.core.models import Base, TimestampMixin
from app.inspections.models import Inspection
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class FileAttachment(TimestampMixin, Base):
    __tablename__ = "file_attachments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    inspection_id: Mapped[UUID] = mapped_column(
        ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)

    inspection: Mapped[Inspection] = relationship("Inspection")
