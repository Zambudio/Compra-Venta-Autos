"""Servicio de fuentes: catálogo, health y ejecución de sincronizaciones.

La sincronización recorre las páginas del conector, normaliza cada anuncio y lo
ingiere (`ListingService`). Una fuente caída no bloquea nada más: los fallos
transitorios se reintentan y, si persisten, el run queda `PARTIAL`/`FAILED` con
un resumen saneado (Plan Maestro §39/§41, ADR-0004, ADR-0012).
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.base import BaseConnector
from app.connectors.errors import TransientConnectorError
from app.connectors.filters import ConnectorSearchFilter
from app.connectors.registry import get_connector
from app.connectors.schemas import ConnectorSearchPage
from app.listings.normalizer import NormalizationError
from app.listings.service import ListingService
from app.listings.vocab import SyncRunStatus
from app.sources.models import Source, SourceComplianceReview, SourceSyncRun
from app.sources.schemas import (
    ComplianceReviewRead,
    SourceHealthRead,
    SourceRead,
    SyncRunRead,
)

_PAGE_SIZE = 50
_MAX_PAGES = 20
_MAX_SEARCH_ATTEMPTS = 3
_TERMINAL = {SyncRunStatus.SUCCESS, SyncRunStatus.PARTIAL, SyncRunStatus.FAILED}


class SourceNotFoundError(Exception):
    def __init__(self, source_key: str) -> None:
        super().__init__(f"unknown source: {source_key}")
        self.source_key = source_key


class SourceInactiveError(Exception):
    def __init__(self, source_key: str) -> None:
        super().__init__(f"source is not active: {source_key}")
        self.source_key = source_key


class SyncRunNotFoundError(Exception):
    def __init__(self, run_id: UUID) -> None:
        super().__init__(f"unknown sync run: {run_id}")
        self.run_id = run_id


class SourceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_sources(self) -> list[SourceRead]:
        sources = (await self.db.execute(select(Source).order_by(Source.key))).scalars().all()
        return [
            SourceRead(
                key=source.key,
                name=source.name,
                provider_kind=source.provider_kind,
                is_active=source.is_active,
                is_automatable=source.is_automatable,
                latest_review=await self._latest_review(source.id),
            )
            for source in sources
        ]

    async def health(self, source_key: str) -> SourceHealthRead:
        connector = get_connector(source_key)
        health = await connector.health_check()
        return SourceHealthRead(
            source_key=health.source_key,
            healthy=health.healthy,
            detail=health.detail,
            checked_at=health.checked_at,
        )

    async def list_sync_runs(
        self, source_key: str, *, limit: int, offset: int
    ) -> list[SyncRunRead]:
        source = await self._require_source(source_key)
        runs = (
            (
                await self.db.execute(
                    select(SourceSyncRun)
                    .where(SourceSyncRun.source_id == source.id)
                    .order_by(SourceSyncRun.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
            )
            .scalars()
            .all()
        )
        return [run_read(run, source_key) for run in runs]

    async def create_run(
        self, source_key: str, *, mode: str, filters: dict[str, object], request_id: str | None
    ) -> SourceSyncRun:
        source = await self._require_source(source_key)
        if not source.is_active:
            raise SourceInactiveError(source_key)
        run = SourceSyncRun(
            source_id=source.id,
            status=SyncRunStatus.PENDING,
            mode=mode,
            filters=filters,
            request_id=request_id,
        )
        self.db.add(run)
        await self.db.flush()
        return run

    async def execute_run(
        self, run_id: UUID, *, connector: BaseConnector | None = None
    ) -> SourceSyncRun:
        run = await self.db.get(SourceSyncRun, run_id)
        if run is None:
            raise SyncRunNotFoundError(run_id)
        if run.status in _TERMINAL:
            return run
        source = await self.db.get(Source, run.source_id)
        assert source is not None
        active_connector = connector or get_connector(source.key)

        run.status = SyncRunStatus.RUNNING
        run.started_at = datetime.now(UTC)
        await self.db.flush()

        listing_service = ListingService(self.db)
        errors: list[str] = []
        seen = created = updated = snapshots = 0

        for page in range(1, _MAX_PAGES + 1):
            connector_filter = _connector_filter(run.filters, page=page, page_size=_PAGE_SIZE)
            try:
                result_page = await _search_with_retry(active_connector, connector_filter)
            except TransientConnectorError as exc:
                errors.append(f"page {page}: {exc}")
                break

            for item in result_page.items:
                seen += 1
                try:
                    outcome = await listing_service.ingest_raw(item, source)
                except NormalizationError as exc:
                    errors.append(f"{item.external_id}: {exc}")
                    continue
                created += int(outcome.created)
                updated += int(outcome.updated)
                snapshots += int(outcome.snapshot_created)

            if not result_page.has_more:
                break

        run.listings_seen = seen
        run.listings_created = created
        run.listings_updated = updated
        run.snapshots_created = snapshots
        run.finished_at = datetime.now(UTC)
        run.error_summary = _sanitize(errors)
        run.status = _final_status(errors=errors, seen=seen, changed=created + updated)
        if created > 0:
            from app.vehicles.service import VehicleService

            await VehicleService.generate_match_candidates(self.db)
        await self.db.flush()
        return run

    async def _require_source(self, source_key: str) -> Source:
        source = (
            await self.db.execute(select(Source).where(Source.key == source_key))
        ).scalar_one_or_none()
        if source is None:
            raise SourceNotFoundError(source_key)
        return source

    async def _latest_review(self, source_id: UUID) -> ComplianceReviewRead | None:
        review = (
            await self.db.execute(
                select(SourceComplianceReview)
                .where(SourceComplianceReview.source_id == source_id)
                .order_by(SourceComplianceReview.checked_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        return ComplianceReviewRead.model_validate(review) if review is not None else None


async def _search_with_retry(
    connector: BaseConnector, connector_filter: ConnectorSearchFilter
) -> ConnectorSearchPage:
    last_error: TransientConnectorError | None = None
    for attempt in range(_MAX_SEARCH_ATTEMPTS):
        try:
            return await connector.search(connector_filter)
        except TransientConnectorError as exc:
            last_error = exc
            await asyncio.sleep(0.05 * (attempt + 1))
    assert last_error is not None
    raise last_error


def _connector_filter(
    filters: dict[str, object], *, page: int, page_size: int
) -> ConnectorSearchFilter:
    from app.sources.schemas import SyncRequest

    return SyncRequest.model_validate(filters).to_connector_filter(page=page, page_size=page_size)


def _final_status(*, errors: list[str], seen: int, changed: int) -> SyncRunStatus:
    if not errors:
        return SyncRunStatus.SUCCESS
    if changed == 0 and seen == 0:
        return SyncRunStatus.FAILED
    return SyncRunStatus.PARTIAL


def _sanitize(errors: list[str]) -> str | None:
    if not errors:
        return None
    return "; ".join(errors)[:500]


def run_read(run: SourceSyncRun, source_key: str) -> SyncRunRead:
    return SyncRunRead(
        id=run.id,
        source_key=source_key,
        status=run.status,
        mode=run.mode,
        listings_seen=run.listings_seen,
        listings_created=run.listings_created,
        listings_updated=run.listings_updated,
        snapshots_created=run.snapshots_created,
        error_summary=run.error_summary,
        started_at=run.started_at,
        finished_at=run.finished_at,
        created_at=run.created_at,
    )
