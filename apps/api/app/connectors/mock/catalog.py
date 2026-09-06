"""Carga del catálogo mock versionado y anonimizado.

`catalog_v1.json` contiene anuncios inventados con marcas y modelos reales de
mercado. Es la única fuente automática prevista para la suite normal (ADR-0006,
`docs/source-compliance.md`).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CATALOG_PATH = Path(__file__).with_name("catalog_v1.json")


@lru_cache(maxsize=1)
def _load() -> tuple[str, tuple[dict[str, Any], ...]]:
    data = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    listings = tuple(dict(entry) for entry in data["listings"])
    return str(data["version"]), listings


def catalog_version() -> str:
    return _load()[0]


def load_catalog() -> tuple[dict[str, Any], ...]:
    """Anuncios del catálogo, ordenados de forma estable por `external_id`."""

    return tuple(sorted(_load()[1], key=lambda entry: str(entry["external_id"])))
