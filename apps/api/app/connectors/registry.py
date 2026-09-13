"""Registro de conectores habilitados.

Solo manual y conectores reales (ADR-0006).
"""

from __future__ import annotations

from app.connectors.base import BaseConnector
from app.connectors.errors import UnknownConnectorError
from app.connectors.manual import ManualEntryConnector
from app.connectors.wallapop import WallapopConnector

_CONNECTORS: dict[str, BaseConnector] = {
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
