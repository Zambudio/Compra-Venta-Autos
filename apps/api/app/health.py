import asyncio
from typing import Literal

from fastapi import APIRouter, Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

from app.auth.dependencies import AuthDependency
from app.core.errors import APIError, ErrorBody

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: str


class SystemStatusResponse(BaseModel):
    api: Literal["available"] = "available"
    postgresql: Literal["available"] = "available"
    redis: Literal["ready"] = "ready"


@router.get("/health/live", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/health/ready",
    response_model=HealthResponse,
    responses={503: {"model": ErrorBody}},
)
async def readiness(request: Request) -> HealthResponse:
    results = await asyncio.gather(
        request.app.state.database.ping(),
        request.app.state.redis.ping(),
        return_exceptions=True,
    )
    if any(isinstance(result, BaseException) for result in results):
        raise APIError(
            status_code=503,
            code="dependencies_unavailable",
            title="Service unavailable",
            detail="One or more required dependencies are unavailable.",
        )
    return HealthResponse(status="ready")


@router.get(
    "/system/status",
    response_model=SystemStatusResponse,
    responses={401: {"model": ErrorBody}, 503: {"model": ErrorBody}},
)
async def system_status(request: Request, auth: AuthDependency) -> SystemStatusResponse:
    del auth
    results = await asyncio.gather(
        request.app.state.database.ping(),
        request.app.state.redis.ping(),
        return_exceptions=True,
    )
    if any(isinstance(result, BaseException) for result in results):
        raise APIError(
            status_code=503,
            code="dependencies_unavailable",
            title="Service unavailable",
            detail="One or more required dependencies are unavailable.",
        )
    return SystemStatusResponse()


@router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
