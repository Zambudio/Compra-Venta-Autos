"""Conector de entrada manual.

No descubre anuncios: el usuario aporta la ficha observada bajo acción humana
(Plan Maestro §8-9). `build_raw` envuelve esa ficha en un `RawListing` que sigue
el mismo camino de normalización e ingesta que el resto.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from app.connectors.base import BaseConnector
from app.connectors.filters import ConnectorSearchFilter
from app.connectors.schemas import ConnectorHealth, ConnectorSearchPage, RawListing
from app.listings.vocab import ProviderKind


class ManualEntryConnector(BaseConnector):
    source_key = "manual"
    provider_kind = ProviderKind.MANUAL
    version = "manual-entry-v1"

    async def search(self, filters: ConnectorSearchFilter) -> ConnectorSearchPage:
        return ConnectorSearchPage(
            items=[],
            page=max(1, filters.page),
            page_size=max(1, filters.page_size),
            total=0,
            has_more=False,
        )

    async def fetch(self, external_id: str) -> RawListing | None:
        return None

    async def health_check(self) -> ConnectorHealth:
        return ConnectorHealth(
            source_key=self.source_key,
            healthy=True,
            detail="entrada manual siempre disponible",
            checked_at=datetime.now(UTC),
        )

    def build_raw(self, submission: Mapping[str, Any]) -> RawListing:
        payload = dict(submission)
        external_id = str(payload["external_id"])
        url = payload.get("url")
        return RawListing(
            source_key=self.source_key,
            external_id=external_id,
            url=str(url) if url else None,
            retrieved_at=datetime.now(UTC),
            connector_version=self.version,
            payload=payload,
        )
