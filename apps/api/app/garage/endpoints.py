from typing import Annotated, Any
from uuid import UUID

from app.auth.dependencies import get_db, require_roles
from app.garage import schemas, service
from app.users.models import UserRole
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/garage", tags=["garage"])

@router.post(
    "/purchase",
    response_model=schemas.OwnedVehicleWithDetails,
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))]
)
async def purchase_vehicle(
    vehicle_in: schemas.OwnedVehicleCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Any:
    try:
        vehicle = await service.purchase_opportunity(db, vehicle_in)
        # Compute financials before returning
        financials = service.compute_financials(vehicle)
        result = schemas.OwnedVehicleWithDetails.model_validate(vehicle)
        result.total_expenses = financials["total_expenses"]
        result.total_cost = financials["total_cost"]
        result.net_profit = financials["net_profit"]
        result.roi_percentage = financials["roi_percentage"]
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

@router.get(
    "/vehicles",
    response_model=list[schemas.OwnedVehicleWithDetails],
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN, UserRole.VIEWER))]
)
async def list_vehicles(db: Annotated[AsyncSession, Depends(get_db)]) -> Any:
    vehicles = await service.list_owned_vehicles(db)
    results = []
    for vehicle in vehicles:
        financials = service.compute_financials(vehicle)
        v_out = schemas.OwnedVehicleWithDetails.model_validate(vehicle)
        v_out.total_expenses = financials["total_expenses"]
        v_out.total_cost = financials["total_cost"]
        v_out.net_profit = financials["net_profit"]
        v_out.roi_percentage = financials["roi_percentage"]
        results.append(v_out)
    return results

@router.get(
    "/vehicles/{vehicle_id}",
    response_model=schemas.OwnedVehicleWithDetails,
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN, UserRole.VIEWER))]
)
async def get_vehicle(vehicle_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]) -> Any:
    vehicle = await service.get_owned_vehicle(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
        
    financials = service.compute_financials(vehicle)
    result = schemas.OwnedVehicleWithDetails.model_validate(vehicle)
    result.total_expenses = financials["total_expenses"]
    result.total_cost = financials["total_cost"]
    result.net_profit = financials["net_profit"]
    result.roi_percentage = financials["roi_percentage"]
    return result

@router.post(
    "/vehicles/{vehicle_id}/expenses",
    response_model=schemas.ExpensePublic,
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))]
)
async def add_expense(
    vehicle_id: UUID,
    expense_in: schemas.ExpenseCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Any:
    # Verify vehicle exists
    vehicle = await service.get_owned_vehicle(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
        
    return await service.add_expense(db, vehicle_id, expense_in)

@router.post(
    "/vehicles/{vehicle_id}/sale",
    response_model=schemas.SalePublic,
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))]
)
async def register_sale(
    vehicle_id: UUID,
    sale_in: schemas.SaleCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Any:
    try:
        return await service.register_sale(db, vehicle_id, sale_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
