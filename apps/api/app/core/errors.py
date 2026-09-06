from __future__ import annotations

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = structlog.get_logger()


class ErrorBody(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str
    code: str
    request_id: str


class APIError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        title: str,
        detail: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.title = title
        self.detail = detail
        self.headers = headers or {}


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unavailable")


def _response(
    request: Request,
    *,
    status_code: int,
    code: str,
    title: str,
    detail: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = ErrorBody(
        title=title,
        status=status_code,
        detail=detail,
        code=code,
        request_id=_request_id(request),
    )
    return JSONResponse(status_code=status_code, content=body.model_dump(), headers=headers)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(APIError)
    async def handle_api_error(request: Request, exc: APIError) -> JSONResponse:
        return _response(
            request,
            status_code=exc.status_code,
            code=exc.code,
            title=exc.title,
            detail=exc.detail,
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        return _response(
            request,
            status_code=422,
            code="validation_error",
            title="Invalid request",
            detail="One or more fields are invalid.",
        )

    @app.exception_handler(HTTPException)
    async def handle_http(request: Request, exc: HTTPException) -> JSONResponse:
        detail = (
            exc.detail if isinstance(exc.detail, str) else "The request could not be completed."
        )
        return _response(
            request,
            status_code=exc.status_code,
            code="http_error",
            title="Request failed",
            detail=detail,
            headers=dict(exc.headers or {}),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error", error_type=type(exc).__name__)
        return _response(
            request,
            status_code=500,
            code="internal_error",
            title="Internal server error",
            detail="The request could not be completed.",
        )
