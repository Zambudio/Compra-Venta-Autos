"""Actor Dramatiq de sincronización de fuentes.

Idempotente por `run_id`: si el run ya está en estado terminal, `execute_run` no
hace nada. El actor abre su propia sesión de base de datos (contexto worker) y
propaga `job_id` implícito de Dramatiq mediante el `run_id`.
"""

from __future__ import annotations

import asyncio
from uuid import UUID

import dramatiq

from app.core.broker import configure_broker
from app.core.config import get_settings
from app.core.database import Database
from app.sources.service import SourceService

configure_broker()


@dramatiq.actor(max_retries=3, min_backoff=5_000, max_backoff=60_000, time_limit=300_000)
def sync_source_actor(source_key: str, run_id: str) -> None:
    del source_key  # el run ya conoce su fuente; se acepta por trazabilidad
    asyncio.run(_execute(run_id))


async def _execute(run_id: str) -> None:
    database = Database(get_settings().database_url)
    try:
        async with database.session_factory() as session:
            await SourceService(session).execute_run(UUID(run_id))
            await session.commit()
    finally:
        await database.close()
