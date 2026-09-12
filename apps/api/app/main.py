from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.auth.router import router as auth_router
from app.core.config import Settings, get_settings
from app.core.database import Database
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.core.redis_client import RedisClient
from app.files.endpoints import router as files_router
from app.garage.endpoints import router as garage_router
from app.health import router as health_router
from app.inspections.endpoints import router as inspections_router
from app.knowledge.router import router as knowledge_router
from app.listings.router import router as listings_router
from app.scoring.router import router as scoring_router
from app.sources.router import router as sources_router
from app.vehicles.router import router as vehicles_router
from app.watchlist.endpoints import router as watchlist_router


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.database = Database(resolved_settings.database_url)
        app.state.redis = RedisClient(resolved_settings.redis_dsn)
        try:
            yield
        finally:
            await app.state.redis.close()
            await app.state.database.close()

    app = FastAPI(
        title="MotorScope API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    app.state.settings = resolved_settings
    app.add_middleware(RequestContextMiddleware, settings=resolved_settings)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=resolved_settings.allowed_hosts)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "X-CSRF-Token", "X-Request-ID"],
    )
    register_error_handlers(app)
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(sources_router, prefix="/api/v1")
    app.include_router(listings_router, prefix="/api/v1")
    app.include_router(vehicles_router, prefix="/api/v1")
    app.include_router(knowledge_router, prefix="/api/v1")
    app.include_router(scoring_router, prefix="/api/v1")
    app.include_router(watchlist_router, prefix="/api/v1")
    app.include_router(inspections_router, prefix="/api/v1")
    app.include_router(files_router, prefix="/api/v1")
    app.include_router(garage_router, prefix="/api/v1")
    return app


app = create_app()
