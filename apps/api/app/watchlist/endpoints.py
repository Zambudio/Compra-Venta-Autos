from typing import Annotated
from uuid import UUID

from app.auth.dependencies import AuthDependency, CsrfDependency, DbDependency
from app.watchlist import schemas, service
from fastapi import APIRouter, HTTPException, Query, status

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.post("/", response_model=schemas.WatchlistEntryPublic, status_code=status.HTTP_201_CREATED)
async def create_watchlist_entry(
    auth: AuthDependency,
    csrf: CsrfDependency,
    entry_in: schemas.WatchlistEntryCreate,
    db: DbDependency,
) -> schemas.WatchlistEntryPublic:
    del auth, csrf
    try:
        entry = await service.create_entry(db, entry_in)
        return schemas.WatchlistEntryPublic.model_validate(entry)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=list[schemas.WatchlistEntryWithOpportunity])
async def list_watchlist(
    auth: AuthDependency,
    db: DbDependency,
    active_only: Annotated[bool, Query()] = True,
) -> list[schemas.WatchlistEntryWithOpportunity]:
    del auth
    entries = await service.get_watchlist(db, active_only=active_only)
    from app.scoring.service import ScoringService

    # Map to schema manually since opportunity is an Opportunity model, we need OpportunityRead
    result = []
    for entry in entries:
        opp_dto = ScoringService.map_to_read(entry.opportunity)
        result.append(
            schemas.WatchlistEntryWithOpportunity(
                id=entry.id,
                opportunity_id=entry.opportunity_id,
                is_active=entry.is_active,
                notes=entry.notes,
                created_at=entry.created_at,
                updated_at=entry.updated_at,
                opportunity=opp_dto,
            )
        )
    return result


@router.get("/{entry_id}", response_model=schemas.WatchlistEntryWithOpportunity)
async def get_watchlist_entry(
    auth: AuthDependency,
    db: DbDependency,
    entry_id: UUID,
) -> schemas.WatchlistEntryWithOpportunity:
    del auth
    entry = await service.get_entry(db, entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist entry not found"
        )

    from app.scoring.service import ScoringService

    opp_dto = ScoringService.map_to_read(entry.opportunity)
    return schemas.WatchlistEntryWithOpportunity(
        id=entry.id,
        opportunity_id=entry.opportunity_id,
        is_active=entry.is_active,
        notes=entry.notes,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        opportunity=opp_dto,
    )


@router.patch("/{entry_id}", response_model=schemas.WatchlistEntryPublic)
async def update_watchlist_entry(
    auth: AuthDependency,
    csrf: CsrfDependency,
    db: DbDependency,
    entry_id: UUID,
    entry_update: schemas.WatchlistEntryUpdate,
) -> schemas.WatchlistEntryPublic:
    del auth, csrf
    entry = await service.update_entry(db, entry_id, entry_update)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist entry not found"
        )
    return schemas.WatchlistEntryPublic.model_validate(entry)
