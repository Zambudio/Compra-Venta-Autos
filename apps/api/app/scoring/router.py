"""Endpoints de la API para perfiles de scoring y oportunidades."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.auth.dependencies import AuthDependency, CsrfDependency, DbDependency, require_roles
from app.core.errors import ErrorBody
from app.scoring.schemas import (
    OpportunityEvaluationRequest,
    OpportunityPage,
    OpportunityRead,
    OpportunityStatusUpdate,
    ScoringProfileCreate,
    ScoringProfileRead,
    ScoringProfileVersionCreate,
    ScoringProfileVersionRead,
)
from app.scoring.service import ScoringService
from app.scoring.vocab import OpportunityStatus, SellerPressureLevel
from app.users.models import UserRole

router = APIRouter(tags=["scoring", "opportunities"])

_MutatingAuth = Annotated[object, Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))]


# --- Perfiles de Scoring ---


@router.get(
    "/scoring/profiles",
    response_model=list[ScoringProfileRead],
    summary="Listar perfiles de scoring",
)
async def list_profiles(
    auth: AuthDependency,
    db: DbDependency,
) -> list[ScoringProfileRead]:
    del auth
    profiles = await ScoringService.list_profiles(db)
    result: list[ScoringProfileRead] = []
    for p in profiles:
        versions_read = [
            ScoringProfileVersionRead.model_validate(v)
            for v in sorted(p.versions, key=lambda x: x.version_number, reverse=True)
        ]
        active_v = versions_read[0] if versions_read else None
        p_read = ScoringProfileRead(
            id=p.id,
            name=p.name,
            slug=p.slug,
            description=p.description,
            is_active=p.is_active,
            created_at=p.created_at,
            updated_at=p.updated_at,
            versions=versions_read,
            active_version=active_v,
        )
        result.append(p_read)
    return result


@router.post(
    "/scoring/profiles",
    response_model=ScoringProfileRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo perfil de scoring",
    responses={409: {"model": ErrorBody, "description": "Slug ya existente"}},
)
async def create_profile(
    auth: _MutatingAuth,
    csrf: CsrfDependency,
    db: DbDependency,
    body: ScoringProfileCreate,
) -> ScoringProfileRead:
    del auth, csrf
    profile = await ScoringService.create_profile(db, body)
    versions_read = [
        ScoringProfileVersionRead.model_validate(v)
        for v in sorted(profile.versions, key=lambda x: x.version_number, reverse=True)
    ]
    active_v = versions_read[0] if versions_read else None
    dto = ScoringProfileRead(
        id=profile.id,
        name=profile.name,
        slug=profile.slug,
        description=profile.description,
        is_active=profile.is_active,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        versions=versions_read,
        active_version=active_v,
    )
    await db.commit()
    return dto


@router.get(
    "/scoring/profiles/{profile_id}",
    response_model=ScoringProfileRead,
    summary="Obtener perfil de scoring por ID",
    responses={404: {"model": ErrorBody, "description": "Perfil no encontrado"}},
)
async def get_profile(
    auth: AuthDependency,
    db: DbDependency,
    profile_id: UUID,
) -> ScoringProfileRead:
    del auth
    profile = await ScoringService.get_profile(db, profile_id)
    versions_read = [
        ScoringProfileVersionRead.model_validate(v)
        for v in sorted(profile.versions, key=lambda x: x.version_number, reverse=True)
    ]
    active_v = versions_read[0] if versions_read else None
    return ScoringProfileRead(
        id=profile.id,
        name=profile.name,
        slug=profile.slug,
        description=profile.description,
        is_active=profile.is_active,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        versions=versions_read,
        active_version=active_v,
    )


@router.post(
    "/scoring/profiles/{profile_id}/versions",
    response_model=ScoringProfileVersionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Añadir nueva versión inmutable a un perfil de scoring",
    responses={404: {"model": ErrorBody, "description": "Perfil no encontrado"}},
)
async def create_profile_version(
    auth: _MutatingAuth,
    csrf: CsrfDependency,
    db: DbDependency,
    profile_id: UUID,
    body: ScoringProfileVersionCreate,
) -> ScoringProfileVersionRead:
    del auth, csrf
    version = await ScoringService.create_profile_version(db, profile_id, body)
    dto = ScoringProfileVersionRead.model_validate(version)
    await db.commit()
    return dto


@router.get(
    "/scoring/versions/{version_id}",
    response_model=ScoringProfileVersionRead,
    summary="Obtener versión de perfil por ID",
    responses={404: {"model": ErrorBody, "description": "Versión no encontrada"}},
)
async def get_profile_version(
    auth: AuthDependency,
    db: DbDependency,
    version_id: UUID,
) -> ScoringProfileVersionRead:
    del auth
    version = await ScoringService.get_profile_version(db, version_id)
    return ScoringProfileVersionRead.model_validate(version)


# --- Oportunidades ---


@router.get(
    "/opportunities",
    response_model=OpportunityPage,
    summary="Listar oportunidades con filtros y paginación",
)
async def list_opportunities(
    auth: AuthDependency,
    db: DbDependency,
    status_filter: Annotated[OpportunityStatus | None, Query(alias="status")] = None,
    min_score: Annotated[Decimal | None, Query(ge=0, le=100)] = None,
    brand: Annotated[str | None, Query()] = None,
    seller_pressure: Annotated[SellerPressureLevel | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> OpportunityPage:
    del auth
    items, total = await ScoringService.list_opportunities(
        db,
        status=status_filter,
        min_score=min_score,
        brand=brand,
        seller_pressure=seller_pressure,
        page=page,
        page_size=page_size,
    )
    has_more = (page * page_size) < total
    read_items = [ScoringService.map_to_read(item) for item in items]
    return OpportunityPage(
        items=read_items,
        page=page,
        page_size=page_size,
        total=total,
        has_more=has_more,
    )


@router.get(
    "/opportunities/{opportunity_id}",
    response_model=OpportunityRead,
    summary="Obtener detalle completo de una oportunidad",
    responses={404: {"model": ErrorBody, "description": "Oportunidad no encontrada"}},
)
async def get_opportunity(
    auth: AuthDependency,
    db: DbDependency,
    opportunity_id: UUID,
) -> OpportunityRead:
    del auth
    opportunity = await ScoringService.get_opportunity(db, opportunity_id)
    return ScoringService.map_to_read(opportunity)


@router.patch(
    "/opportunities/{opportunity_id}/status",
    response_model=OpportunityRead,
    summary="Actualizar estado de una oportunidad",
    responses={404: {"model": ErrorBody, "description": "Oportunidad no encontrada"}},
)
async def update_opportunity_status(
    auth: _MutatingAuth,
    csrf: CsrfDependency,
    db: DbDependency,
    opportunity_id: UUID,
    body: OpportunityStatusUpdate,
) -> OpportunityRead:
    del auth, csrf
    opportunity = await ScoringService.update_opportunity_status(
        db, opportunity_id, body.status, body.notes
    )
    dto = ScoringService.map_to_read(opportunity)
    await db.commit()
    return dto


@router.post(
    "/opportunities/evaluate/listing/{listing_id}",
    response_model=OpportunityRead,
    summary="Evaluar oportunidad sobre un anuncio",
    responses={404: {"model": ErrorBody, "description": "Anuncio no encontrado"}},
)
async def evaluate_listing_opportunity(
    auth: _MutatingAuth,
    csrf: CsrfDependency,
    db: DbDependency,
    listing_id: UUID,
    body: OpportunityEvaluationRequest | None = None,
) -> OpportunityRead:
    del auth, csrf
    profile_version_id = body.profile_version_id if body else None
    opportunity = await ScoringService.evaluate_listing(
        db, listing_id, profile_version_id=profile_version_id
    )
    dto = ScoringService.map_to_read(opportunity)
    await db.commit()
    return dto


@router.post(
    "/opportunities/evaluate/vehicle/{vehicle_id}",
    response_model=OpportunityRead,
    summary="Evaluar oportunidad sobre un vehículo",
    responses={404: {"model": ErrorBody, "description": "Vehículo no encontrado"}},
)
async def evaluate_vehicle_opportunity(
    auth: _MutatingAuth,
    csrf: CsrfDependency,
    db: DbDependency,
    vehicle_id: UUID,
    body: OpportunityEvaluationRequest | None = None,
) -> OpportunityRead:
    del auth, csrf
    profile_version_id = body.profile_version_id if body else None
    opportunity = await ScoringService.evaluate_vehicle(
        db, vehicle_id, profile_version_id=profile_version_id
    )
    dto = ScoringService.map_to_read(opportunity)
    await db.commit()
    return dto
