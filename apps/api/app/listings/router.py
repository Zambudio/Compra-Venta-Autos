"""Endpoints de anuncios: búsqueda, detalle y alta manual."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.auth.dependencies import AuthDependency, CsrfDependency, DbDependency, require_roles
from app.core.errors import APIError, ErrorBody
from app.listings.schemas import ListingDetailRead, ListingPage, ListingRead, ManualListingCreate
from app.listings.service import (
    DuplicateManualListingError,
    ListingNotFoundError,
    ListingService,
)
from app.search.schemas import SearchFilter
from app.users.models import UserRole

router = APIRouter(prefix="/listings", tags=["listings"])

_MutatingAuth = Annotated[object, Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))]


@router.get("", response_model=ListingPage)
async def search_listings(
    auth: AuthDependency,
    db: DbDependency,
    criteria: Annotated[SearchFilter, Query()],
) -> ListingPage:
    del auth
    return await ListingService(db).search(criteria)


@router.get(
    "/{listing_id}",
    response_model=ListingDetailRead,
    responses={404: {"model": ErrorBody}},
)
async def get_listing(
    listing_id: UUID, auth: AuthDependency, db: DbDependency
) -> ListingDetailRead:
    del auth
    try:
        return await ListingService(db).get_detail(listing_id)
    except ListingNotFoundError as exc:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="listing_not_found",
            title="Not Found",
            detail="No existe ese anuncio.",
        ) from exc


@router.post(
    "/manual",
    response_model=ListingRead,
    status_code=status.HTTP_201_CREATED,
    responses={403: {"model": ErrorBody}, 409: {"model": ErrorBody}, 422: {"model": ErrorBody}},
)
async def create_manual_listing(
    payload: ManualListingCreate,
    auth: CsrfDependency,
    db: DbDependency,
    _roles: _MutatingAuth,
) -> ListingRead:
    del auth
    try:
        listing = await ListingService(db).create_manual(payload)
    except DuplicateManualListingError as exc:
        raise APIError(
            status_code=status.HTTP_409_CONFLICT,
            code="listing_already_exists",
            title="Conflict",
            detail="Ese vehículo ya está registrado manualmente.",
        ) from exc
    await db.commit()
    return listing
