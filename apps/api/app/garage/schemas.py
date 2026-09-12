from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.garage.models import ExpenseCategory
from pydantic import BaseModel, ConfigDict


class ExpenseBase(BaseModel):
    amount: Decimal
    category: ExpenseCategory
    description: str
    expense_date: datetime
    receipt_file_id: UUID | None = None

class ExpenseCreate(ExpenseBase):
    pass

class ExpensePublic(ExpenseBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    vehicle_id: UUID
    created_at: datetime
    updated_at: datetime

class SaleBase(BaseModel):
    sale_price: Decimal
    sale_date: datetime
    buyer_info: str | None = None
    notes: str | None = None

class SaleCreate(SaleBase):
    pass

class SalePublic(SaleBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    vehicle_id: UUID
    created_at: datetime
    updated_at: datetime

class OwnedVehicleBase(BaseModel):
    opportunity_id: UUID
    purchase_price: Decimal
    purchase_date: datetime
    vin: str | None = None
    license_plate: str | None = None
    notes: str | None = None

class OwnedVehicleCreate(BaseModel):
    opportunity_id: UUID
    purchase_price: Decimal
    purchase_date: datetime | None = None
    vin: str | None = None
    license_plate: str | None = None
    notes: str | None = None

class OwnedVehiclePublic(OwnedVehicleBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime

class OwnedVehicleWithDetails(OwnedVehiclePublic):
    expenses: list[ExpensePublic]
    sale: SalePublic | None = None
    # Derived fields calculated dynamically
    total_expenses: Decimal
    total_cost: Decimal
    net_profit: Decimal | None = None
    roi_percentage: Decimal | None = None
