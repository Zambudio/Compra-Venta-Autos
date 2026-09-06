"""Endpoints de vehículos, matching asistido, histórico y valoraciones de mercado."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.auth.dependencies import AuthDependency, CsrfDependency, DbDependency, require_roles
from app.core.errors import APIError, ErrorBody
from app.users.models import UserRole
from app.vehicles.errors import (
    MatchCandidateAlreadyDecidedError,
    MatchCandidateNotFoundError,
    VehicleNotFoundError,
)
from app.vehicles.schemas import (
    ConfirmMatchResponse,
    MarketEstimateRead,
    MatchCandidatePage,
    MatchCandidateRead,
    RejectMatchResponse,
    VehicleDetailRead,
    VehicleHistoryMetrics,
    VehicleListingSummary,
    VehiclePage,
    VehicleRead,
)
from app.vehicles.service import VehicleService
from app.vehicles.vocab import MatchCandidateStatus

router = APIRouter(tags=["vehicles"])

_MutatingAuth = Annotated[object, Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))]


# --- Match Candidates ---


@router.get(
    "/match-candidates",
    response_model=MatchCandidatePage,
    summary="Listar candidatos a coincidencia de vehículos",
)
async def list_match_candidates(
    auth: AuthDependency,
    db: DbDependency,
    status_filter: Annotated[
        MatchCandidateStatus | None, Query(alias="status")
    ] = MatchCandidateStatus.PENDING,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> MatchCandidatePage:
    del auth
    items, total = await VehicleService.list_match_candidates(
        db, status=status_filter, page=page, page_size=page_size
    )
    has_more = (page * page_size) < total
    candidate_reads = [MatchCandidateRead.model_validate(item) for item in items]
    return MatchCandidatePage(
        items=candidate_reads,
        page=page,
        page_size=page_size,
        total=total,
        has_more=has_more,
    )


@router.post(
    "/match-candidates/generate",
    status_code=status.HTTP_200_OK,
    summary="Disparar detección de candidatos de matching asistido",
    responses={403: {"model": ErrorBody}},
)
async def generate_match_candidates(
    auth: CsrfDependency,
    db: DbDependency,
    _roles: _MutatingAuth,
) -> dict[str, int]:
    del auth
    created = await VehicleService.generate_match_candidates(db)
    await db.commit()
    return {"created_candidates": created}


@router.post(
    "/match-candidates/{candidate_id}/confirm",
    response_model=ConfirmMatchResponse,
    summary="Confirmar emparejamiento de anuncios",
    responses={
        403: {"model": ErrorBody},
        404: {"model": ErrorBody},
        409: {"model": ErrorBody},
    },
)
async def confirm_match_candidate(
    candidate_id: UUID,
    auth: CsrfDependency,
    db: DbDependency,
    _roles: _MutatingAuth,
) -> ConfirmMatchResponse:
    try:
        candidate = await VehicleService.confirm_match(
            db, candidate_id=candidate_id, user_id=auth.user.id
        )
    except MatchCandidateNotFoundError as exc:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="match_candidate_not_found",
            title="Not Found",
            detail=f"Candidato {candidate_id} no encontrado.",
        ) from exc
    except MatchCandidateAlreadyDecidedError as exc:
        raise APIError(
            status_code=status.HTTP_409_CONFLICT,
            code="match_candidate_already_decided",
            title="Conflict",
            detail=f"El candidato ya fue resuelto previamente con estado {exc.current_status}.",
        ) from exc

    await db.commit()
    assert candidate.listing_a.vehicle_id is not None
    return ConfirmMatchResponse(
        candidate_id=candidate.id,
        status=candidate.status,
        vehicle_id=candidate.listing_a.vehicle_id,
    )


@router.post(
    "/match-candidates/{candidate_id}/reject",
    response_model=RejectMatchResponse,
    summary="Rechazar emparejamiento de anuncios",
    responses={
        403: {"model": ErrorBody},
        404: {"model": ErrorBody},
        409: {"model": ErrorBody},
    },
)
async def reject_match_candidate(
    candidate_id: UUID,
    auth: CsrfDependency,
    db: DbDependency,
    _roles: _MutatingAuth,
) -> RejectMatchResponse:
    try:
        candidate = await VehicleService.reject_match(
            db, candidate_id=candidate_id, user_id=auth.user.id
        )
    except MatchCandidateNotFoundError as exc:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="match_candidate_not_found",
            title="Not Found",
            detail=f"Candidato {candidate_id} no encontrado.",
        ) from exc
    except MatchCandidateAlreadyDecidedError as exc:
        raise APIError(
            status_code=status.HTTP_409_CONFLICT,
            code="match_candidate_already_decided",
            title="Conflict",
            detail=f"El candidato ya fue resuelto previamente con estado {exc.current_status}.",
        ) from exc

    await db.commit()
    return RejectMatchResponse(
        candidate_id=candidate.id,
        status=candidate.status,
    )


# --- Vehicles ---


@router.get(
    "/vehicles",
    response_model=VehiclePage,
    summary="Listar vehículos unificados",
)
async def list_vehicles(
    auth: AuthDependency,
    db: DbDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    brand: Annotated[str | None, Query()] = None,
    model: Annotated[str | None, Query()] = None,
) -> VehiclePage:
    del auth
    items, total = await VehicleService.list_vehicles(
        db, page=page, page_size=page_size, brand=brand, model=model
    )
    has_more = (page * page_size) < total
    return VehiclePage(
        items=[VehicleRead.model_validate(v) for v in items],
        page=page,
        page_size=page_size,
        total=total,
        has_more=has_more,
    )


@router.get(
    "/vehicles/{vehicle_id}",
    response_model=VehicleDetailRead,
    summary="Obtener detalle de vehículo unificado",
    responses={404: {"model": ErrorBody}},
)
async def get_vehicle(
    vehicle_id: UUID,
    auth: AuthDependency,
    db: DbDependency,
) -> VehicleDetailRead:
    del auth
    try:
        vehicle = await VehicleService.get_vehicle_detail(db, vehicle_id=vehicle_id)
    except VehicleNotFoundError as exc:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="vehicle_not_found",
            title="Not Found",
            detail=f"Vehículo {vehicle_id} no encontrado.",
        ) from exc

    history_metrics = await VehicleService.get_vehicle_history(db, vehicle_id=vehicle_id)
    latest_estimate = vehicle.estimates[-1] if vehicle.estimates else None

    return VehicleDetailRead(
        id=vehicle.id,
        brand=vehicle.brand,
        model=vehicle.model,
        generation=vehicle.generation,
        trim=vehicle.trim,
        engine_code=vehicle.engine_code,
        power_kw=vehicle.power_kw,
        fuel_type=vehicle.fuel_type,
        transmission=vehicle.transmission,
        year=vehicle.year,
        first_listed_at=vehicle.first_listed_at,
        listing_count=vehicle.listing_count,
        created_at=vehicle.created_at,
        updated_at=vehicle.updated_at,
        listings=[VehicleListingSummary.model_validate(item) for item in vehicle.listings],
        history=history_metrics,
        market_estimate=MarketEstimateRead.model_validate(latest_estimate)
        if latest_estimate
        else None,
    )


@router.get(
    "/vehicles/{vehicle_id}/history",
    response_model=VehicleHistoryMetrics,
    summary="Obtener métricas consolidadas del histórico de un vehículo",
    responses={404: {"model": ErrorBody}},
)
async def get_vehicle_history(
    vehicle_id: UUID,
    auth: AuthDependency,
    db: DbDependency,
) -> VehicleHistoryMetrics:
    del auth
    try:
        return await VehicleService.get_vehicle_history(db, vehicle_id=vehicle_id)
    except VehicleNotFoundError as exc:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="vehicle_not_found",
            title="Not Found",
            detail=f"Vehículo {vehicle_id} no encontrado.",
        ) from exc


@router.post(
    "/vehicles/{vehicle_id}/market-estimate",
    response_model=MarketEstimateRead,
    summary="Calcular y guardar estimación de mercado para un vehículo",
    responses={
        403: {"model": ErrorBody},
        404: {"model": ErrorBody},
    },
)
async def compute_vehicle_market_estimate(
    vehicle_id: UUID,
    auth: CsrfDependency,
    db: DbDependency,
    _roles: _MutatingAuth,
    min_comparables: Annotated[int, Query(ge=1)] = 3,
) -> MarketEstimateRead:
    del auth
    try:
        estimate = await VehicleService.compute_and_save_market_estimate(
            db, vehicle_id=vehicle_id, min_comparables=min_comparables
        )
    except VehicleNotFoundError as exc:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="vehicle_not_found",
            title="Not Found",
            detail=f"Vehículo {vehicle_id} no encontrado.",
        ) from exc

    await db.commit()
    return MarketEstimateRead.model_validate(estimate)
