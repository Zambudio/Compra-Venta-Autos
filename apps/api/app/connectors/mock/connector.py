"""Conector Mock: catálogo determinista con filtros, paginación y fallos simulados."""

from __future__ import annotations

import asyncio
import hashlib
from datetime import UTC, datetime
from typing import Any

from app.connectors.base import BaseConnector
from app.connectors.errors import TransientConnectorError
from app.connectors.filters import ConnectorSearchFilter
from app.connectors.mock.catalog import catalog_version, load_catalog
from app.connectors.schemas import ConnectorHealth, ConnectorSearchPage, RawListing
from app.listings.vocab import ProviderKind, parse_fuel_type, parse_seller_type

_MAX_PAGE_SIZE = 100


class MockConnector(BaseConnector):
    source_key = "mock"
    provider_kind = ProviderKind.MOCK
    version = "mock-catalog-v1"

    def __init__(self, *, latency_enabled: bool = True, faults_enabled: bool = True) -> None:
        self._latency_enabled = latency_enabled
        self._faults_enabled = faults_enabled

    async def search(self, filters: ConnectorSearchFilter) -> ConnectorSearchPage:
        await self._simulate_latency(filters)
        self._maybe_fail(filters)

        matches = [entry for entry in load_catalog() if _matches(entry, filters)]
        page_size = max(1, min(filters.page_size, _MAX_PAGE_SIZE))
        page = max(1, filters.page)
        start = (page - 1) * page_size
        window = matches[start : start + page_size]

        return ConnectorSearchPage(
            items=[self._to_raw(entry) for entry in window],
            page=page,
            page_size=page_size,
            total=len(matches),
            has_more=start + page_size < len(matches),
        )

    async def fetch(self, external_id: str) -> RawListing | None:
        await self._simulate_latency(ConnectorSearchFilter())
        for entry in load_catalog():
            if str(entry["external_id"]) == external_id:
                return self._to_raw(entry)
        return None

    async def health_check(self) -> ConnectorHealth:
        return ConnectorHealth(
            source_key=self.source_key,
            healthy=True,
            detail=f"catálogo {catalog_version()} con {len(load_catalog())} anuncios",
            checked_at=datetime.now(UTC),
        )

    def _to_raw(self, entry: dict[str, Any]) -> RawListing:
        return RawListing(
            source_key=self.source_key,
            external_id=str(entry["external_id"]),
            url=entry.get("url"),
            retrieved_at=datetime.now(UTC),
            connector_version=self.version,
            payload=dict(entry),
        )

    async def _simulate_latency(self, filters: ConnectorSearchFilter) -> None:
        if not self._latency_enabled:
            return
        seed = f"{filters.brand}:{filters.model}:{filters.page}".encode()
        jitter = int(hashlib.sha256(seed).hexdigest(), 16) % 80 / 1000
        await asyncio.sleep(0.02 + jitter)

    def _maybe_fail(self, filters: ConnectorSearchFilter) -> None:
        if self._faults_enabled and filters.page % 4 == 0:
            raise TransientConnectorError(
                f"fuente mock no disponible temporalmente (página {filters.page})"
            )


def _matches(entry: dict[str, Any], filters: ConnectorSearchFilter) -> bool:
    if filters.brand and str(entry["marca"]).casefold() != filters.brand.casefold():
        return False
    if filters.model and filters.model.casefold() not in str(entry["modelo"]).casefold():
        return False
    if filters.year_min is not None and int(entry["anio"]) < filters.year_min:
        return False
    if filters.year_max is not None and int(entry["anio"]) > filters.year_max:
        return False
    if filters.price_min is not None and int(entry["precio"]) < filters.price_min:
        return False
    if filters.price_max is not None and int(entry["precio"]) > filters.price_max:
        return False
    if filters.mileage_max is not None and int(entry["km"]) > filters.mileage_max:
        return False
    if (
        filters.fuel_type is not None
        and parse_fuel_type(entry.get("combustible")) != filters.fuel_type
    ):
        return False
    if (
        filters.seller_type is not None
        and parse_seller_type(entry.get("vendedor")) != filters.seller_type
    ):
        return False
    if (
        filters.province
        and str(entry.get("provincia", "")).casefold() != filters.province.casefold()
    ):
        return False
    return True
