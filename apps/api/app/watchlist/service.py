from uuid import UUID

from app.scoring.models import Opportunity
from app.watchlist import models, schemas
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


async def create_entry(
    db: AsyncSession, entry_in: schemas.WatchlistEntryCreate
) -> models.WatchlistEntry:
    # Check if opportunity exists
    stmt = select(Opportunity).where(Opportunity.id == entry_in.opportunity_id)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise ValueError("Opportunity not found")

    entry = models.WatchlistEntry(**entry_in.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def get_watchlist(db: AsyncSession, active_only: bool = True) -> list[models.WatchlistEntry]:
    stmt = select(models.WatchlistEntry).options(selectinload(models.WatchlistEntry.opportunity))
    if active_only:
        stmt = stmt.where(models.WatchlistEntry.is_active.is_(True))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_entry(db: AsyncSession, entry_id: UUID) -> models.WatchlistEntry | None:
    stmt = (
        select(models.WatchlistEntry)
        .options(selectinload(models.WatchlistEntry.opportunity))
        .where(models.WatchlistEntry.id == entry_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_entry(
    db: AsyncSession, entry_id: UUID, entry_update: schemas.WatchlistEntryUpdate
) -> models.WatchlistEntry | None:
    entry = await get_entry(db, entry_id)
    if not entry:
        return None
    for field, value in entry_update.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    await db.commit()
    await db.refresh(entry)
    return entry
