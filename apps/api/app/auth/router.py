from fastapi import APIRouter, Request, Response, status

from app.auth.dependencies import (
    AuthDependency,
    CsrfDependency,
    DbDependency,
    RedisDependency,
    SettingsDependency,
)
from app.auth.rate_limit import LoginRateLimiter
from app.auth.schemas import LoginRequest, LogoutResponse, UserResponse
from app.auth.service import AuthService, normalize_email
from app.core.errors import APIError, ErrorBody

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=UserResponse,
    responses={401: {"model": ErrorBody}, 429: {"model": ErrorBody}},
)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: DbDependency,
    redis: RedisDependency,
    settings: SettingsDependency,
) -> UserResponse:
    client_ip = request.client.host if request.client else "unknown"
    limiter = LoginRateLimiter(redis, settings.login_rate_limit, settings.login_rate_window_seconds)
    if not await limiter.check(client_ip, normalize_email(str(payload.email))):
        raise APIError(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="login_rate_limited",
            title="Too many requests",
            detail="Too many login attempts. Try again later.",
            headers={"Retry-After": str(settings.login_rate_window_seconds)},
        )

    auth_session = await AuthService(db, settings.session_ttl_seconds).login(
        str(payload.email), payload.password, request.state.request_id
    )
    if auth_session is None:
        raise APIError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_credentials",
            title="Unauthorized",
            detail="The email or password is invalid.",
        )

    response.set_cookie(
        settings.session_cookie_name,
        auth_session.session_token,
        max_age=settings.session_ttl_seconds,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )
    response.set_cookie(
        settings.csrf_cookie_name,
        auth_session.csrf_token,
        max_age=settings.session_ttl_seconds,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=False,
        samesite="lax",
    )
    return UserResponse.model_validate(auth_session.user)


@router.get(
    "/me",
    response_model=UserResponse,
    responses={401: {"model": ErrorBody}},
)
async def me(auth: AuthDependency) -> UserResponse:
    return UserResponse.model_validate(auth.user)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    responses={401: {"model": ErrorBody}, 403: {"model": ErrorBody}},
)
async def logout(
    request: Request,
    response: Response,
    auth: CsrfDependency,
    db: DbDependency,
    settings: SettingsDependency,
) -> LogoutResponse:
    await AuthService(db, settings.session_ttl_seconds).logout(
        auth.session, auth.user, request.state.request_id
    )
    response.delete_cookie(
        settings.session_cookie_name,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )
    response.delete_cookie(
        settings.csrf_cookie_name,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=False,
        samesite="lax",
    )
    return LogoutResponse()
