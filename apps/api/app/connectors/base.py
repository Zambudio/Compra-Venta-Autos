"""Contrato común de conector (ADR-0006).

Un conocedor de la semántica de una fuente. El *provider* (medio de adquisición:
API, feed, importación manual, navegador autorizado) queda encapsulado en la
implementación concreta. En el MVP solo existen `MockConnector` y
`ManualEntryConnector`; ningún conector de portal real está activo.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from app.connectors.filters import ConnectorSearchFilter
from app.connectors.schemas import ConnectorHealth, ConnectorSearchPage, RawListing
from app.listings.vocab import ProviderKind


class BaseConnector(ABC):
    source_key: ClassVar[str]
    provider_kind: ClassVar[ProviderKind]
    version: ClassVar[str]

    @abstractmethod
    async def search(self, filters: ConnectorSearchFilter) -> ConnectorSearchPage:
        """Devuelve una página de anuncios observados que cumplen el filtro."""

    @abstractmethod
    async def fetch(self, external_id: str) -> RawListing | None:
        """Devuelve un anuncio concreto o `None` si la fuente no lo expone."""

    @abstractmethod
    async def health_check(self) -> ConnectorHealth:
        """Estado del conector para observabilidad (Plan Maestro §41)."""
