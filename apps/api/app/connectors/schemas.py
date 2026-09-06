"""Tipos del contrato de conector (ADR-0006).

Un `RawListing` es lo observado tal cual: el `payload` es el diccionario original
de la fuente y no se transforma aquí. El normalizador (`app.listings.normalizer`)
es el único que produce el esquema interno.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RawListing(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_key: str
    external_id: str
    url: str | None
    retrieved_at: datetime
    connector_version: str
    payload: dict[str, Any]


class ConnectorSearchPage(BaseModel):
    items: list[RawListing]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    has_more: bool


class ConnectorHealth(BaseModel):
    source_key: str
    healthy: bool
    detail: str
    checked_at: datetime
