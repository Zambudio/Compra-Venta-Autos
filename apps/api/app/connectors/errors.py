"""Errores del subsistema de adquisición."""

from __future__ import annotations


class ConnectorError(Exception):
    """Fallo general de un conector."""


class TransientConnectorError(ConnectorError):
    """Fallo temporal: el llamador puede reintentar con backoff (Plan Maestro §39)."""


class UnknownConnectorError(ConnectorError):
    """Se pidió un conector que no está registrado."""

    def __init__(self, source_key: str) -> None:
        super().__init__(f"unknown connector: {source_key}")
        self.source_key = source_key
