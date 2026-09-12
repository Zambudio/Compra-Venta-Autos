from typing import Annotated
from uuid import UUID

from app.auth.dependencies import AuthDependency, CsrfDependency, DbDependency
from app.inspections import schemas, service
from fastapi import APIRouter, HTTPException, Query, status

router = APIRouter(prefix="/inspections", tags=["inspections"])


@router.post("/", response_model=schemas.InspectionPublic, status_code=status.HTTP_201_CREATED)
async def create_inspection(
    auth: AuthDependency,
    csrf: CsrfDependency,
    inspection_in: schemas.InspectionCreate,
    db: DbDependency,
) -> schemas.InspectionPublic:
    del auth, csrf
    inspection = await service.create_inspection(db, inspection_in)
    return schemas.InspectionPublic.model_validate(inspection)


@router.get("/", response_model=list[schemas.InspectionWithDetails])
async def list_inspections(
    auth: AuthDependency,
    db: DbDependency,
    watchlist_entry_id: Annotated[UUID | None, Query()] = None,
) -> list[schemas.InspectionWithDetails]:
    del auth
    inspections = await service.list_inspections(db, watchlist_entry_id)
    return [schemas.InspectionWithDetails.model_validate(i) for i in inspections]


@router.get("/{inspection_id}", response_model=schemas.InspectionWithDetails)
async def get_inspection(
    auth: AuthDependency,
    db: DbDependency,
    inspection_id: UUID,
) -> schemas.InspectionWithDetails:
    del auth
    inspection = await service.get_inspection(db, inspection_id)
    if not inspection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")
    return schemas.InspectionWithDetails.model_validate(inspection)


@router.patch("/{inspection_id}", response_model=schemas.InspectionPublic)
async def update_inspection(
    auth: AuthDependency,
    csrf: CsrfDependency,
    db: DbDependency,
    inspection_id: UUID,
    inspection_update: schemas.InspectionUpdate,
) -> schemas.InspectionPublic:
    del auth, csrf
    inspection = await service.update_inspection(db, inspection_id, inspection_update)
    if not inspection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")
    return schemas.InspectionPublic.model_validate(inspection)


@router.post(
    "/{inspection_id}/checks",
    response_model=schemas.InspectionCheckPublic,
    status_code=status.HTTP_201_CREATED,
)
async def add_inspection_check(
    auth: AuthDependency,
    csrf: CsrfDependency,
    db: DbDependency,
    inspection_id: UUID,
    check_in: schemas.InspectionCheckCreate,
) -> schemas.InspectionCheckPublic:
    del auth, csrf
    # Ensure inspection exists
    inspection = await service.get_inspection(db, inspection_id)
    if not inspection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")

    check = await service.add_check(db, inspection_id, check_in)
    return schemas.InspectionCheckPublic.model_validate(check)


@router.patch("/checks/{check_id}", response_model=schemas.InspectionCheckPublic)
async def update_inspection_check(
    auth: AuthDependency,
    csrf: CsrfDependency,
    db: DbDependency,
    check_id: UUID,
    check_update: schemas.InspectionCheckUpdate,
) -> schemas.InspectionCheckPublic:
    del auth, csrf
    check = await service.update_check(db, check_id, check_update)
    if not check:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Check not found")
    return schemas.InspectionCheckPublic.model_validate(check)
