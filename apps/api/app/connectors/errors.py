"""Errores del subsistema de adquisición."""

from __future__ import annotations


class ConnectorError(Exception):
    """Fallo general de un conector."""


class TransientConnectorError(ConnectorError):
    """Fallo temporal: el llamador puede reintentar con backoff (Plan Maestro §39)."""


class ConnectorAccessDeniedError(TransientConnectorError):
    """El proveedor rechazó las credenciales o bloqueó el acceso (403)."""


class ConnectorRateLimitError(TransientConnectorError):
    """El proveedor agotó su cuota y comunicó cuándo reintentar."""

    def __init__(self, message: str, *, retry_after_seconds: int = 60) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class UnknownConnectorError(ConnectorError):
    """Se pidió un conector que no está registrado."""

    def __init__(self, source_key: str) -> None:
        super().__init__(f"unknown connector: {source_key}")
        self.source_key = source_key
