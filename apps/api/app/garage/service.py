from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.garage import models, schemas
from app.scoring.models import Opportunity
from app.scoring.vocab import OpportunityStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


async def purchase_opportunity(
    db: AsyncSession, vehicle_in: schemas.OwnedVehicleCreate
) -> models.OwnedVehicle:
    # Get opportunity
    stmt = select(Opportunity).where(Opportunity.id == vehicle_in.opportunity_id)
    result = await db.execute(stmt)
    opportunity = result.scalar_one_or_none()
    
    if not opportunity:
        raise ValueError("Opportunity not found")
        
    if opportunity.status == OpportunityStatus.PURCHASED:
        raise ValueError("Opportunity is already purchased")

    # Change opportunity status
    opportunity.status = OpportunityStatus.PURCHASED

    # Create owned vehicle
    owned_vehicle = models.OwnedVehicle(
        opportunity_id=vehicle_in.opportunity_id,
        purchase_price=vehicle_in.purchase_price,
        purchase_date=vehicle_in.purchase_date or datetime.now(UTC),
        vin=vehicle_in.vin,
        license_plate=vehicle_in.license_plate,
        notes=vehicle_in.notes
    )
    
    db.add(owned_vehicle)
    await db.commit()
    await db.refresh(owned_vehicle)
    
    # We load relations for returning full object
    return await get_owned_vehicle(db, owned_vehicle.id) # type: ignore

async def get_owned_vehicle(db: AsyncSession, vehicle_id: UUID) -> models.OwnedVehicle | None:
    stmt = (
        select(models.OwnedVehicle)
        .options(selectinload(models.OwnedVehicle.expenses), selectinload(models.OwnedVehicle.sale))
        .where(models.OwnedVehicle.id == vehicle_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def list_owned_vehicles(db: AsyncSession) -> list[models.OwnedVehicle]:
    stmt = (
        select(models.OwnedVehicle)
        .options(selectinload(models.OwnedVehicle.expenses), selectinload(models.OwnedVehicle.sale))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def add_expense(
    db: AsyncSession, vehicle_id: UUID, expense_in: schemas.ExpenseCreate
) -> models.Expense:
    expense = models.Expense(
        **expense_in.model_dump(),
        vehicle_id=vehicle_id
    )
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return expense

async def register_sale(
    db: AsyncSession, vehicle_id: UUID, sale_in: schemas.SaleCreate
) -> models.Sale:
    # Check if sale already exists
    vehicle = await get_owned_vehicle(db, vehicle_id)
    if not vehicle:
        raise ValueError("Vehicle not found")
    if vehicle.sale:
        raise ValueError("Vehicle is already sold")
        
    sale = models.Sale(
        **sale_in.model_dump(),
        vehicle_id=vehicle_id
    )
    db.add(sale)
    
    # Update opportunity status to SOLD
    stmt = select(Opportunity).where(Opportunity.id == vehicle.opportunity_id)
    opp_result = await db.execute(stmt)
    opportunity = opp_result.scalar_one_or_none()
    if opportunity:
        opportunity.status = OpportunityStatus.SOLD
        
    await db.commit()
    await db.refresh(sale)
    return sale

def compute_financials(vehicle: models.OwnedVehicle) -> dict[str, Any]:
    total_expenses = sum((expense.amount for expense in vehicle.expenses), Decimal(0))
    total_cost = vehicle.purchase_price + total_expenses
    
    net_profit = None
    roi_percentage = None
    
    if vehicle.sale:
        net_profit = vehicle.sale.sale_price - total_cost
        if total_cost > 0:
            roi_percentage = (net_profit / total_cost) * 100
            
    return {
        "total_expenses": total_expenses,
        "total_cost": total_cost,
        "net_profit": net_profit,
        "roi_percentage": roi_percentage
    }
