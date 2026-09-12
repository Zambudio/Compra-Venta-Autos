from datetime import UTC, datetime
from uuid import UUID

from app.inspections import models, schemas
from app.inspections.vocab import InspectionStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


async def create_inspection(
    db: AsyncSession, inspection_in: schemas.InspectionCreate
) -> models.Inspection:
    inspection = models.Inspection(**inspection_in.model_dump(), status=InspectionStatus.DRAFT)
    db.add(inspection)
    await db.commit()
    await db.refresh(inspection)
    return inspection


async def get_inspection(db: AsyncSession, inspection_id: UUID) -> models.Inspection | None:
    stmt = (
        select(models.Inspection)
        .options(selectinload(models.Inspection.checks))
        .where(models.Inspection.id == inspection_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_inspections(
    db: AsyncSession, watchlist_entry_id: UUID | None = None
) -> list[models.Inspection]:
    stmt = select(models.Inspection).options(selectinload(models.Inspection.checks))
    if watchlist_entry_id:
        stmt = stmt.where(models.Inspection.watchlist_entry_id == watchlist_entry_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_inspection(
    db: AsyncSession, inspection_id: UUID, inspection_update: schemas.InspectionUpdate
) -> models.Inspection | None:
    inspection = await get_inspection(db, inspection_id)
    if not inspection:
        return None

    update_data = inspection_update.model_dump(exclude_unset=True)

    # Handle status transition to COMPLETED
    if (
        update_data.get("status") == InspectionStatus.COMPLETED
        and inspection.status != InspectionStatus.COMPLETED
    ):
        inspection.completed_at = datetime.now(UTC)
    elif update_data.get("status") and update_data.get("status") != InspectionStatus.COMPLETED:
        inspection.completed_at = None

    for field, value in update_data.items():
        setattr(inspection, field, value)

    await db.commit()
    await db.refresh(inspection)
    return inspection


async def add_check(
    db: AsyncSession, inspection_id: UUID, check_in: schemas.InspectionCheckCreate
) -> models.InspectionCheck:
    check = models.InspectionCheck(**check_in.model_dump(), inspection_id=inspection_id)
    db.add(check)
    await db.commit()
    await db.refresh(check)
    return check


async def get_check(db: AsyncSession, check_id: UUID) -> models.InspectionCheck | None:
    stmt = select(models.InspectionCheck).where(models.InspectionCheck.id == check_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_check(
    db: AsyncSession, check_id: UUID, check_update: schemas.InspectionCheckUpdate
) -> models.InspectionCheck | None:
    check = await get_check(db, check_id)
    if not check:
        return None
    for field, value in check_update.model_dump(exclude_unset=True).items():
        setattr(check, field, value)
    await db.commit()
    await db.refresh(check)
    return check
