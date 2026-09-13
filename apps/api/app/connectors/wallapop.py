"""Conector real para la API de Wallapop."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

from app.connectors.base import BaseConnector
from app.connectors.errors import TransientConnectorError
from app.connectors.filters import ConnectorSearchFilter
from app.connectors.schemas import ConnectorHealth, ConnectorSearchPage, RawListing
from app.listings.vocab import ProviderKind


class WallapopConnector(BaseConnector):
    source_key = "wallapop"
    provider_kind = ProviderKind.CONNECTOR
    version = "wallapop-api-v3"
    
    _BASE_URL = "https://api.wallapop.com/api/v3/cars/search"

    def __init__(self, proxy_url: str | None = None) -> None:
        self.proxy_url = proxy_url

    async def search(self, filters: ConnectorSearchFilter) -> ConnectorSearchPage:
        params = self._build_params(filters)
        
        async with httpx.AsyncClient(proxy=self.proxy_url) as client:
            try:
                response = await client.get(
                    self._BASE_URL,
                    params=params,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "X-DeviceOS": "0"},
                    timeout=15.0
                )
                if response.status_code == 403:
                    raise TransientConnectorError("Acceso bloqueado por Wallapop (403): puede ser rate limit o bloqueo anti-bot")
                if response.status_code == 429:
                    raise TransientConnectorError("Demasiadas solicitudes a Wallapop (429): intenta más tarde")
                if response.status_code >= 500:
                    raise TransientConnectorError(f"Error en servidor Wallapop ({response.status_code})")
                response.raise_for_status()
            except httpx.TimeoutException as e:
                raise TransientConnectorError(f"Timeout contactando Wallapop: {e}") from e
            except httpx.HTTPError as e:
                raise TransientConnectorError(f"Error HTTP contactando Wallapop: {e}") from e

        data = response.json()
        objects = data.get("search_objects", [])
        
        # Wallapop no devuelve el "total" fácilmente a veces, estimamos
        return ConnectorSearchPage(
            items=[self._to_raw(obj) for obj in objects],
            page=filters.page,
            page_size=filters.page_size,
            total=len(objects), # Esto se debería inferir de metadatos si los devuelve
            has_more=len(objects) == filters.page_size
        )

    async def fetch(self, external_id: str) -> RawListing | None:
        async with httpx.AsyncClient(proxy=self.proxy_url) as client:
            try:
                # Endpoint de item específico de Wallapop v3
                response = await client.get(
                    f"https://api.wallapop.com/api/v3/items/{external_id}",
                    headers={"User-Agent": "Mozilla/5.0", "X-DeviceOS": "0"},
                    timeout=10.0
                )
                if response.status_code == 404:
                    return None
                if response.status_code == 403:
                    raise TransientConnectorError("Acceso bloqueado por Wallapop (403)")
                if response.status_code == 429:
                    raise TransientConnectorError("Demasiadas solicitudes a Wallapop (429)")
                if response.status_code >= 500:
                    raise TransientConnectorError(f"Error en servidor Wallapop ({response.status_code})")
                response.raise_for_status()
            except httpx.TimeoutException as e:
                raise TransientConnectorError(f"Timeout fetching from Wallapop: {e}") from e
            except httpx.HTTPError as e:
                raise TransientConnectorError(f"Error fetching from Wallapop: {e}") from e
                
        return self._to_raw(response.json())

    async def health_check(self) -> ConnectorHealth:
        try:
            # Una petición mínima para ver si estamos bloqueados
            async with httpx.AsyncClient(proxy=self.proxy_url) as client:
                res = await client.get(
                    self._BASE_URL,
                    params={"keywords": "test"},
                    headers={"User-Agent": "Mozilla/5.0", "X-DeviceOS": "0"},
                    timeout=5.0
                )
                if res.status_code == 200:
                    healthy = True
                    detail = "API accesible"
                elif res.status_code == 403:
                    healthy = False
                    detail = "Bloqueado (403): rate limit o anti-bot"
                elif res.status_code == 429:
                    healthy = False
                    detail = "Demasiadas solicitudes (429)"
                elif res.status_code >= 500:
                    healthy = False
                    detail = f"Error servidor ({res.status_code})"
                else:
                    healthy = False
                    detail = f"Error HTTP {res.status_code}"
        except httpx.TimeoutException:
            healthy = False
            detail = "Timeout conectando con API"
        except Exception as e:
            healthy = False
            detail = f"Error: {str(e)}"
            
        return ConnectorHealth(
            source_key=self.source_key,
            healthy=healthy,
            detail=detail,
            checked_at=datetime.now(UTC)
        )

    def _build_params(self, filters: ConnectorSearchFilter) -> dict[str, Any]:
        # Wallapop params pagination
        params: dict[str, Any] = {
            "start": (filters.page - 1) * filters.page_size,
            "step": filters.page_size,
        }
        
        if filters.brand:
            params["brand"] = filters.brand
        if filters.model:
            params["model"] = filters.model
        if filters.year_min:
            params["min_year"] = filters.year_min
        if filters.year_max:
            params["max_year"] = filters.year_max
        if filters.price_min:
            params["min_sale_price"] = filters.price_min
        if filters.price_max:
            params["max_sale_price"] = filters.price_max
            
        return params

    def _to_raw(self, item: dict[str, Any]) -> RawListing:
        return RawListing(
            source_key=self.source_key,
            external_id=item.get("id", str(item.get("item_id", ""))),
            url=item.get("web_slug", ""),
            retrieved_at=datetime.now(UTC),
            connector_version=self.version,
            payload=item
        )
