import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.core.models import Base, TimestampMixin
from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship


class ExpenseCategory(str, Enum):
    REPAIR = "REPAIR"
    TRANSPORT = "TRANSPORT"
    TAX = "TAX"
    FEE = "FEE"
    OTHER = "OTHER"

class OwnedVehicle(TimestampMixin, Base):
    __tablename__ = "owned_vehicles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("opportunities.id"), unique=True)
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    purchase_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    vin: Mapped[str | None] = mapped_column(String, nullable=True)
    license_plate: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    

    expenses: Mapped[list[Expense]] = relationship(back_populates="vehicle", cascade="all, delete-orphan")
    sale: Mapped[Sale | None] = relationship(back_populates="vehicle", cascade="all, delete-orphan", uselist=False)

class Expense(TimestampMixin, Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("owned_vehicles.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    category: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    expense_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    receipt_file_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("file_attachments.id"), nullable=True)


    vehicle: Mapped[OwnedVehicle] = relationship(back_populates="expenses")

class Sale(TimestampMixin, Base):
    __tablename__ = "sales"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("owned_vehicles.id"), unique=True)
    sale_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    sale_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    buyer_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


    vehicle: Mapped[OwnedVehicle] = relationship(back_populates="sale")
