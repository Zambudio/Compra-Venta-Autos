"""Registro de conectores habilitados.

Solo mock y manual (ADR-0006, docs/source-compliance.md). La instancia de
MockConnector del registro simula latencia realista pero no fallos aleatorios;
los tests instancian su propio conector para probar reintentos.
"""

from __future__ import annotations

from app.connectors.base import BaseConnector
from app.connectors.errors import UnknownConnectorError
from app.connectors.manual import ManualEntryConnector
from app.connectors.mock.connector import MockConnector
from app.connectors.wallapop import WallapopConnector

_CONNECTORS: dict[str, BaseConnector] = {
    "mock": MockConnector(latency_enabled=True, faults_enabled=False),
    "manual": ManualEntryConnector(),
    "wallapop": WallapopConnector(),
}


def get_connector(source_key: str) -> BaseConnector:
    try:
        return _CONNECTORS[source_key]
    except KeyError:
        raise UnknownConnectorError(source_key) from None


def available_source_keys() -> tuple[str, ...]:
    return tuple(_CONNECTORS)
