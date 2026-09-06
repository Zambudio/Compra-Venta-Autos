"""Endpoints de fuentes: catálogo, health y sincronización."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.auth.dependencies import AuthDependency, CsrfDependency, DbDependency, require_roles
from app.connectors.errors import UnknownConnectorError
from app.core.errors import APIError, ErrorBody
from app.sources.schemas import (
    SourceHealthRead,
    SourceRead,
    SyncMode,
    SyncRequest,
    SyncRunRead,
)
from app.sources.service import (
    SourceInactiveError,
    SourceNotFoundError,
    SourceService,
    run_read,
)
from app.users.models import UserRole

router = APIRouter(prefix="/sources", tags=["sources"])

_MutatingAuth = Annotated[object, Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))]


@router.get("", response_model=list[SourceRead])
async def list_sources(auth: AuthDependency, db: DbDependency) -> list[SourceRead]:
    del auth
    return await SourceService(db).list_sources()


@router.get(
    "/{source_key}/health",
    response_model=SourceHealthRead,
    responses={404: {"model": ErrorBody}},
)
async def source_health(
    source_key: str, auth: AuthDependency, db: DbDependency
) -> SourceHealthRead:
    del auth
    try:
        return await SourceService(db).health(source_key)
    except UnknownConnectorError as exc:
        raise _not_found(exc.source_key) from exc


@router.get(
    "/{source_key}/sync-runs",
    response_model=list[SyncRunRead],
    responses={404: {"model": ErrorBody}},
)
async def list_sync_runs(
    source_key: str,
    auth: AuthDependency,
    db: DbDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[SyncRunRead]:
    del auth
    try:
        return await SourceService(db).list_sync_runs(source_key, limit=limit, offset=offset)
    except SourceNotFoundError as exc:
        raise _not_found(exc.source_key) from exc


@router.post(
    "/{source_key}/sync",
    response_model=SyncRunRead,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        403: {"model": ErrorBody},
        404: {"model": ErrorBody},
        409: {"model": ErrorBody},
    },
)
async def sync_source(
    source_key: str,
    request: Request,
    auth: CsrfDependency,
    db: DbDependency,
    _roles: _MutatingAuth,
    mode: Annotated[SyncMode, Query()] = SyncMode.SYNC,
    payload: SyncRequest | None = None,
) -> SyncRunRead:
    del auth
    service = SourceService(db)
    request_filter = payload or SyncRequest()
    try:
        run = await service.create_run(
            source_key,
            mode=mode.value,
            filters=request_filter.as_filter_dict(),
            request_id=request.state.request_id,
        )
    except SourceNotFoundError as exc:
        raise _not_found(exc.source_key) from exc
    except SourceInactiveError as exc:
        raise APIError(
            status_code=status.HTTP_409_CONFLICT,
            code="source_inactive",
            title="Conflict",
            detail=f"La fuente '{exc.source_key}' no está activa.",
        ) from exc

    if mode is SyncMode.ASYNC:
        result = run_read(run, source_key)
        await db.commit()
        _enqueue(source_key, str(run.id))
        return result

    executed = await service.execute_run(run.id)
    result = run_read(executed, source_key)
    await db.commit()
    return result


def _enqueue(source_key: str, run_id: str) -> None:
    from app.sources.tasks import sync_source_actor

    sync_source_actor.send(source_key, run_id)


def _not_found(source_key: str) -> APIError:
    return APIError(
        status_code=status.HTTP_404_NOT_FOUND,
        code="source_not_found",
        title="Not Found",
        detail=f"No existe la fuente '{source_key}'.",
    )
