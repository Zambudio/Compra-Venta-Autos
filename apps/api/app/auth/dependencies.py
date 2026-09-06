from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Coroutine
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated, Any, cast

from fastapi import Depends, Header, Request
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import AuthSession
from app.auth.security import hash_token, tokens_match
from app.core.config import Settings
from app.core.errors import APIError
from app.users.models import User, UserRole


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    async for session in request.app.state.database.session():
        yield session


def get_redis(request: Request) -> Redis:
    return cast(Redis, request.app.state.redis.client)


def get_settings_dependency(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


DbDependency = Annotated[AsyncSession, Depends(get_db)]
RedisDependency = Annotated[Redis, Depends(get_redis)]
SettingsDependency = Annotated[Settings, Depends(get_settings_dependency)]


@dataclass(frozen=True, slots=True)
class AuthContext:
    user: User
    session: AuthSession


async def require_auth(request: Request, db: DbDependency) -> AuthContext:
    settings: Settings = request.app.state.settings
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise _unauthorized()
    statement = (
        select(AuthSession, User)
        .join(User, User.id == AuthSession.user_id)
        .where(AuthSession.token_hash == hash_token(token))
    )
    result = await db.execute(statement)
    row = result.tuples().one_or_none()
    if row is None:
        raise _unauthorized()
    session, user = row
    if (
        session.revoked_at is not None
        or session.expires_at <= datetime.now(UTC)
        or not user.is_active
    ):
        raise _unauthorized()
    return AuthContext(user=user, session=session)


AuthDependency = Annotated[AuthContext, Depends(require_auth)]


async def require_csrf(
    request: Request,
    auth: AuthDependency,
    csrf_header: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> AuthContext:
    settings: Settings = request.app.state.settings
    csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
    if (
        csrf_header is None
        or csrf_cookie is None
        or not tokens_match(csrf_header, csrf_cookie)
        or not tokens_match(hash_token(csrf_header), auth.session.csrf_token_hash)
    ):
        raise APIError(
            status_code=403,
            code="csrf_failed",
            title="Forbidden",
            detail="The CSRF token is missing or invalid.",
        )
    return auth


CsrfDependency = Annotated[AuthContext, Depends(require_csrf)]


def require_roles(
    *allowed: UserRole,
) -> Callable[[AuthContext], Coroutine[Any, Any, AuthContext]]:
    async def dependency(auth: AuthDependency) -> AuthContext:
        if auth.user.role not in allowed:
            raise APIError(
                status_code=403,
                code="forbidden",
                title="Forbidden",
                detail="You do not have permission to perform this action.",
            )
        return auth

    return dependency


def _unauthorized() -> APIError:
    return APIError(
        status_code=401,
        code="authentication_required",
        title="Unauthorized",
        detail="Authentication is required.",
    )
