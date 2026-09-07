"""Endpoints de la API de Knowledge Base, evidencias y fiabilidad."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.auth.dependencies import AuthDependency, CsrfDependency, DbDependency, require_roles
from app.core.errors import APIError, ErrorBody
from app.knowledge.errors import (
    IssueCannotBeVerifiedWithoutEvidenceError,
    KnowledgeSourceNotFoundError,
    KnownIssueNotFoundError,
    ManufacturerNotFoundError,
    VehicleModelNotFoundError,
)
from app.knowledge.schemas import (
    EngineCreate,
    EngineRead,
    EvidenceCreate,
    EvidencePage,
    EvidenceRead,
    KnowledgeSourceCreate,
    KnowledgeSourcePage,
    KnowledgeSourceRead,
    KnownIssueCreate,
    KnownIssueDetailRead,
    KnownIssuePage,
    KnownIssueRead,
    KnownIssueUpdate,
    ManufacturerCreate,
    ManufacturerRead,
    ReliabilityLookupResponse,
    TransmissionSpecCreate,
    TransmissionSpecRead,
    VehicleClassificationCreate,
    VehicleClassificationPage,
    VehicleClassificationRead,
    VehicleGenerationCreate,
    VehicleGenerationRead,
    VehicleMitigationCreate,
    VehicleMitigationRead,
    VehicleModelCreate,
    VehicleModelRead,
)
from app.knowledge.service import KnowledgeService
from app.knowledge.vocab import (
    ClassificationStatus,
    ClassificationTargetType,
    IssueSeverity,
    IssueStatus,
    VehicleComponent,
)
from app.listings.vocab import FuelType
from app.users.models import UserRole
from app.vehicles.errors import VehicleNotFoundError
from app.vehicles.service import VehicleService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

_MutatingAuth = Annotated[object, Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))]


# --- Jerarquía Técnica ---


@router.get("/manufacturers", response_model=list[ManufacturerRead], summary="Listar fabricantes")
async def list_manufacturers(
    auth: AuthDependency, db: DbDependency, skip: int = 0, limit: int = 100
) -> list[ManufacturerRead]:
    del auth
    items = await KnowledgeService.list_manufacturers(db, skip=skip, limit=limit)
    return [ManufacturerRead.model_validate(m) for m in items]


@router.post(
    "/manufacturers",
    response_model=ManufacturerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear fabricante",
    responses={403: {"model": ErrorBody}},
)
async def create_manufacturer(
    data: ManufacturerCreate, auth: CsrfDependency, db: DbDependency, _roles: _MutatingAuth
) -> ManufacturerRead:
    del auth
    m = await KnowledgeService.create_manufacturer(db, data)
    await db.commit()
    return ManufacturerRead.model_validate(m)


@router.get("/models", response_model=list[VehicleModelRead], summary="Listar modelos")
async def list_models(
    auth: AuthDependency, db: DbDependency, manufacturer_id: UUID | None = None
) -> list[VehicleModelRead]:
    del auth
    items = await KnowledgeService.list_models(db, manufacturer_id=manufacturer_id)
    return [VehicleModelRead.model_validate(m) for m in items]


@router.post(
    "/models",
    response_model=VehicleModelRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear modelo de vehículo",
    responses={403: {"model": ErrorBody}, 404: {"model": ErrorBody}},
)
async def create_model(
    data: VehicleModelCreate, auth: CsrfDependency, db: DbDependency, _roles: _MutatingAuth
) -> VehicleModelRead:
    del auth
    try:
        model = await KnowledgeService.create_model(db, data)
        await db.commit()
        return VehicleModelRead.model_validate(model)
    except ManufacturerNotFoundError as exc:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="manufacturer_not_found",
            title="Not Found",
            detail=str(exc),
        ) from exc


@router.get(
    "/generations", response_model=list[VehicleGenerationRead], summary="Listar generaciones"
)
async def list_generations(
    auth: AuthDependency, db: DbDependency, model_id: UUID | None = None
) -> list[VehicleGenerationRead]:
    del auth
    items = await KnowledgeService.list_generations(db, model_id=model_id)
    return [VehicleGenerationRead.model_validate(g) for g in items]


@router.post(
    "/generations",
    response_model=VehicleGenerationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear generación de modelo",
    responses={403: {"model": ErrorBody}, 404: {"model": ErrorBody}},
)
async def create_generation(
    data: VehicleGenerationCreate, auth: CsrfDependency, db: DbDependency, _roles: _MutatingAuth
) -> VehicleGenerationRead:
    del auth
    try:
        gen = await KnowledgeService.create_generation(db, data)
        await db.commit()
        return VehicleGenerationRead.model_validate(gen)
    except VehicleModelNotFoundError as exc:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="model_not_found",
            title="Not Found",
            detail=str(exc),
        ) from exc


@router.get("/engines", response_model=list[EngineRead], summary="Listar motores")
async def list_engines(
    auth: AuthDependency,
    db: DbDependency,
    manufacturer_id: UUID | None = None,
    fuel_type: FuelType | None = None,
) -> list[EngineRead]:
    del auth
    items = await KnowledgeService.list_engines(
        db, manufacturer_id=manufacturer_id, fuel_type=fuel_type
    )
    return [EngineRead.model_validate(e) for e in items]


@router.post(
    "/engines",
    response_model=EngineRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear motor",
    responses={403: {"model": ErrorBody}, 404: {"model": ErrorBody}},
)
async def create_engine(
    data: EngineCreate, auth: CsrfDependency, db: DbDependency, _roles: _MutatingAuth
) -> EngineRead:
    del auth
    try:
        eng = await KnowledgeService.create_engine(db, data)
        await db.commit()
        return EngineRead.model_validate(eng)
    except ManufacturerNotFoundError as exc:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="manufacturer_not_found",
            title="Not Found",
            detail=str(exc),
        ) from exc


@router.get(
    "/transmissions", response_model=list[TransmissionSpecRead], summary="Listar transmisiones"
)
async def list_transmissions(auth: AuthDependency, db: DbDependency) -> list[TransmissionSpecRead]:
    del auth
    items = await KnowledgeService.list_transmissions(db)
    return [TransmissionSpecRead.model_validate(t) for t in items]


@router.post(
    "/transmissions",
    response_model=TransmissionSpecRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear especificación de transmisión",
    responses={403: {"model": ErrorBody}},
)
async def create_transmission(
    data: TransmissionSpecCreate, auth: CsrfDependency, db: DbDependency, _roles: _MutatingAuth
) -> TransmissionSpecRead:
    del auth
    trans = await KnowledgeService.create_transmission(db, data)
    await db.commit()
    return TransmissionSpecRead.model_validate(trans)


# --- Fuentes y Evidencias ---


@router.get("/sources", response_model=KnowledgeSourcePage, summary="Listar fuentes documentales")
async def list_sources(
    auth: AuthDependency,
    db: DbDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> KnowledgeSourcePage:
    del auth
    items, total = await KnowledgeService.list_sources(db, page=page, page_size=page_size)
    return KnowledgeSourcePage(
        items=[KnowledgeSourceRead.model_validate(s) for s in items],
        page=page,
        page_size=page_size,
        total=total,
        has_more=(page * page_size) < total,
    )


@router.post(
    "/sources",
    response_model=KnowledgeSourceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar fuente documental",
    responses={403: {"model": ErrorBody}},
)
async def create_source(
    data: KnowledgeSourceCreate, auth: CsrfDependency, db: DbDependency, _roles: _MutatingAuth
) -> KnowledgeSourceRead:
    del auth
    src = await KnowledgeService.create_source(db, data)
    await db.commit()
    return KnowledgeSourceRead.model_validate(src)


@router.get("/evidences", response_model=EvidencePage, summary="Listar evidencias técnicas")
async def list_evidences(
    auth: AuthDependency,
    db: DbDependency,
    component: VehicleComponent | None = None,
    verified_only: bool = False,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> EvidencePage:
    del auth
    items, total = await KnowledgeService.list_evidences(
        db, component=component, verified_only=verified_only, page=page, page_size=page_size
    )
    return EvidencePage(
        items=[EvidenceRead.model_validate(e) for e in items],
        page=page,
        page_size=page_size,
        total=total,
        has_more=(page * page_size) < total,
    )


@router.post(
    "/evidences",
    response_model=EvidenceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar evidencia técnica",
    responses={403: {"model": ErrorBody}, 404: {"model": ErrorBody}},
)
async def create_evidence(
    data: EvidenceCreate, auth: CsrfDependency, db: DbDependency, _roles: _MutatingAuth
) -> EvidenceRead:
    del auth
    try:
        ev = await KnowledgeService.create_evidence(db, data)
        await db.commit()
        return EvidenceRead.model_validate(ev)
    except KnowledgeSourceNotFoundError as exc:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="source_not_found",
            title="Not Found",
            detail=str(exc),
        ) from exc


# --- Problemas Conocidos ---


@router.get(
    "/issues", response_model=KnownIssuePage, summary="Listar problemas mecánicos conocidos"
)
async def list_known_issues(
    auth: AuthDependency,
    db: DbDependency,
    component: VehicleComponent | None = None,
    severity: IssueSeverity | None = None,
    issue_status: Annotated[IssueStatus | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> KnownIssuePage:
    del auth
    items, total = await KnowledgeService.list_known_issues(
        db,
        component=component,
        severity=severity,
        status=issue_status,
        page=page,
        page_size=page_size,
    )
    return KnownIssuePage(
        items=[KnownIssueRead.model_validate(i) for i in items],
        page=page,
        page_size=page_size,
        total=total,
        has_more=(page * page_size) < total,
    )


@router.post(
    "/issues",
    response_model=KnownIssueRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar problema mecánico conocido",
    responses={400: {"model": ErrorBody}, 403: {"model": ErrorBody}},
)
async def create_known_issue(
    data: KnownIssueCreate, auth: CsrfDependency, db: DbDependency, _roles: _MutatingAuth
) -> KnownIssueRead:
    try:
        issue = await KnowledgeService.create_known_issue(db, data, user_id=auth.user.id)
        await db.commit()
        return KnownIssueRead.model_validate(issue)
    except IssueCannotBeVerifiedWithoutEvidenceError as exc:
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="issue_requires_evidence",
            title="Bad Request",
            detail=str(exc),
        ) from exc


@router.get(
    "/issues/{issue_id}",
    response_model=KnownIssueDetailRead,
    summary="Obtener detalle de un problema mecánico con sus evidencias",
    responses={404: {"model": ErrorBody}},
)
async def get_known_issue(
    issue_id: UUID, auth: AuthDependency, db: DbDependency
) -> KnownIssueDetailRead:
    del auth
    try:
        issue = await KnowledgeService.get_known_issue_detail(db, issue_id)
        return KnownIssueDetailRead.model_validate(issue)
    except KnownIssueNotFoundError as exc:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="known_issue_not_found",
            title="Not Found",
            detail=str(exc),
        ) from exc


@router.patch(
    "/issues/{issue_id}",
    response_model=KnownIssueRead,
    summary="Actualizar problema mecánico conocido",
    responses={400: {"model": ErrorBody}, 403: {"model": ErrorBody}, 404: {"model": ErrorBody}},
)
async def update_known_issue(
    issue_id: UUID,
    data: KnownIssueUpdate,
    auth: CsrfDependency,
    db: DbDependency,
    _roles: _MutatingAuth,
) -> KnownIssueRead:
    try:
        issue = await KnowledgeService.update_known_issue(db, issue_id, data, user_id=auth.user.id)
        await db.commit()
        return KnownIssueRead.model_validate(issue)
    except KnownIssueNotFoundError as exc:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="known_issue_not_found",
            title="Not Found",
            detail=str(exc),
        ) from exc
    except IssueCannotBeVerifiedWithoutEvidenceError as exc:
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="issue_requires_evidence",
            title="Bad Request",
            detail=str(exc),
        ) from exc


# --- Clasificaciones ---


@router.get(
    "/classifications",
    response_model=VehicleClassificationPage,
    summary="Listar clasificaciones de fiabilidad",
)
async def list_classifications(
    auth: AuthDependency,
    db: DbDependency,
    classification_status: Annotated[ClassificationStatus | None, Query(alias="status")] = None,
    target_type: ClassificationTargetType | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> VehicleClassificationPage:
    del auth
    items, total = await KnowledgeService.list_classifications(
        db, status=classification_status, target_type=target_type, page=page, page_size=page_size
    )
    return VehicleClassificationPage(
        items=[VehicleClassificationRead.model_validate(c) for c in items],
        page=page,
        page_size=page_size,
        total=total,
        has_more=(page * page_size) < total,
    )


@router.post(
    "/classifications",
    response_model=VehicleClassificationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear clasificación de fiabilidad",
    responses={403: {"model": ErrorBody}},
)
async def create_classification(
    data: VehicleClassificationCreate, auth: CsrfDependency, db: DbDependency, _roles: _MutatingAuth
) -> VehicleClassificationRead:
    del auth
    c = await KnowledgeService.create_classification(db, data)
    await db.commit()
    return VehicleClassificationRead.model_validate(c)


# --- Diagnóstico y Lookup de Fiabilidad ---


@router.get(
    "/reliability-lookup",
    response_model=ReliabilityLookupResponse,
    summary="Consultar fiabilidad por marca, modelo y año",
)
async def lookup_reliability(
    auth: AuthDependency,
    db: DbDependency,
    brand: Annotated[str, Query(min_length=1)],
    model: Annotated[str, Query(min_length=1)],
    year: int | None = None,
    fuel_type: str | None = None,
    engine_code: str | None = None,
) -> ReliabilityLookupResponse:
    del auth
    return await KnowledgeService.lookup_vehicle_reliability(
        db, brand=brand, model=model, year=year, fuel_type=fuel_type, engine_code=engine_code
    )


@router.get(
    "/vehicles/{vehicle_id}/reliability",
    response_model=ReliabilityLookupResponse,
    summary="Diagnóstico de fiabilidad para un vehículo unificado",
    responses={404: {"model": ErrorBody}},
)
async def get_vehicle_reliability(
    vehicle_id: UUID, auth: AuthDependency, db: DbDependency
) -> ReliabilityLookupResponse:
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

    return await KnowledgeService.lookup_vehicle_reliability(
        db,
        brand=vehicle.brand,
        model=vehicle.model,
        year=vehicle.year,
        fuel_type=vehicle.fuel_type.value if vehicle.fuel_type else None,
        engine_code=vehicle.engine_code,
    )


# --- Mitigaciones en Vehículos Concretos ---


@router.get(
    "/vehicles/{vehicle_id}/mitigations",
    response_model=list[VehicleMitigationRead],
    summary="Listar mitigaciones acreditadas en un vehículo",
)
async def list_vehicle_mitigations(
    vehicle_id: UUID, auth: AuthDependency, db: DbDependency
) -> list[VehicleMitigationRead]:
    del auth
    items = await KnowledgeService.list_vehicle_mitigations(db, vehicle_id=vehicle_id)
    return [VehicleMitigationRead.model_validate(m) for m in items]


@router.post(
    "/vehicles/{vehicle_id}/mitigations",
    response_model=VehicleMitigationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Acreditar mitigación en un vehículo",
    responses={403: {"model": ErrorBody}},
)
async def add_vehicle_mitigation(
    vehicle_id: UUID,
    data: VehicleMitigationCreate,
    auth: CsrfDependency,
    db: DbDependency,
    _roles: _MutatingAuth,
) -> VehicleMitigationRead:
    data.vehicle_id = vehicle_id
    mit = await KnowledgeService.add_vehicle_mitigation(db, data, user_id=auth.user.id)
    await db.commit()
    return VehicleMitigationRead.model_validate(mit)
