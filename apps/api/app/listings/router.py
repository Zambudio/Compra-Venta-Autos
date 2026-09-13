"""Endpoints de anuncios: búsqueda, detalle y alta manual."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.auth.dependencies import (
    AuthDependency,
    CsrfDependency,
    DbDependency,
    RedisDependency,
    require_roles,
)
from app.core.errors import APIError, ErrorBody
from app.listings.schemas import (
    ListingDetailRead,
    ListingPage,
    ListingRead,
    LiveSearchFilters,
    LiveSearchResult,
    ManualListingCreate,
)
from app.listings.service import (
    DuplicateManualListingError,
    ListingNotFoundError,
    ListingService,
    LiveSearchProviderError,
    LiveSearchRateLimitError,
    LiveSourceDisabledError,
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


@router.post(
    "/search",
    response_model=LiveSearchResult,
    responses={
        429: {"model": ErrorBody},
        502: {"model": ErrorBody},
        503: {"model": ErrorBody},
    },
)
async def search_live_listings(
    auth: AuthDependency,
    db: DbDependency,
    cache: RedisDependency,
    criteria: Annotated[LiveSearchFilters, Query()],
) -> LiveSearchResult:
    del auth
    try:
        result = await ListingService(db).search_live(criteria, cache=cache)
    except LiveSourceDisabledError as exc:
        raise APIError(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="source_disabled",
            title="Source unavailable",
            detail=f"El conector '{exc.source_key}' está deshabilitado.",
        ) from exc
    except LiveSearchRateLimitError as exc:
        await db.commit()
        raise APIError(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="search_rate_limited",
            title="Too many requests",
            detail="Se ha alcanzado el límite de búsquedas. Inténtalo más tarde.",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    except LiveSearchProviderError as exc:
        await db.commit()
        code = (
            "source_access_denied"
            if exc.reason == "access_denied"
            else "source_temporarily_unavailable"
        )
        raise APIError(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code=code,
            title="Upstream source error",
            detail="Wallapop no está disponible temporalmente.",
        ) from exc
    await db.commit()
    return result


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
