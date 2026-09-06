"""Normalizador: convierte un payload observado en el esquema interno único.

Función pura, sin I/O. Cualquier fuente (Mock, Manual y en el futuro conectores
autorizados) entrega un `payload` con el mismo vocabulario de claves y el
normalizador produce un `NormalizedListing`. No se confía en los datos del
anunciante: los campos que no se pueden resolver quedan en `None` y nunca se
inventan valores (Plan Maestro §11, §58; ADR-0006).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.listings.vocab import (
    FuelType,
    SellerType,
    Transmission,
    canonical_brand,
    parse_fuel_type,
    parse_seller_type,
    parse_transmission,
)

_MIN_YEAR = 1950
_CV_TO_KW = Decimal("0.7355")

_REQUIRED_STR_KEYS = ("external_id", "marca", "modelo")


class NormalizationError(ValueError):
    """El payload observado no puede convertirse en un anuncio válido."""


class NormalizedListing(BaseModel):
    """Representación interna única de un anuncio observado."""

    model_config = ConfigDict(frozen=True)

    source_key: str
    external_id: str
    url: str | None
    brand: str
    model: str
    generation: str | None
    trim: str | None
    engine_code: str | None
    power_kw: int | None
    fuel_type: FuelType
    transmission: Transmission
    year: int
    mileage_km: int
    price_amount: Decimal
    price_currency: str
    location: str | None
    province: str | None
    seller_type: SellerType
    description: str | None
    image_urls: list[str]
    published_at: datetime | None


def payload_hash(payload: Mapping[str, Any]) -> str:
    """SHA-256 hex del payload en forma canónica (claves ordenadas, sin espacios)."""

    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normalize(payload: Mapping[str, Any], source_key: str) -> NormalizedListing:
    """Convierte un payload observado en `NormalizedListing` o lanza `NormalizationError`."""

    for key in _REQUIRED_STR_KEYS:
        if not _optional_str(payload, key):
            raise NormalizationError(f"missing required field: {key}")

    year = _require_int(payload, "anio")
    mileage = _require_int(payload, "km")
    price = _require_decimal(payload, "precio")

    current_year = datetime.now(UTC).year
    if not _MIN_YEAR <= year <= current_year + 1:
        raise NormalizationError(f"year out of range: {year}")
    if mileage < 0:
        raise NormalizationError("mileage_km must be >= 0")
    if price <= 0:
        raise NormalizationError("price_amount must be > 0")

    power_cv = _optional_int(payload, "potencia_cv")
    power_kw = (
        int((Decimal(power_cv) * _CV_TO_KW).to_integral_value(rounding=ROUND_HALF_UP))
        if power_cv is not None
        else None
    )

    currency = _optional_str(payload, "moneda") or "EUR"

    return NormalizedListing(
        source_key=source_key,
        external_id=_optional_str(payload, "external_id") or "",
        url=_optional_str(payload, "url"),
        brand=canonical_brand(_optional_str(payload, "marca") or ""),
        model=" ".join((_optional_str(payload, "modelo") or "").split()),
        generation=_optional_str(payload, "generacion"),
        trim=_optional_str(payload, "version"),
        engine_code=_optional_str(payload, "codigo_motor"),
        power_kw=power_kw,
        fuel_type=parse_fuel_type(_optional_str(payload, "combustible")),
        transmission=parse_transmission(_optional_str(payload, "cambio")),
        year=year,
        mileage_km=mileage,
        price_amount=price,
        price_currency=currency.upper(),
        location=_optional_str(payload, "poblacion"),
        province=_optional_str(payload, "provincia"),
        seller_type=parse_seller_type(_optional_str(payload, "vendedor")),
        description=_optional_str(payload, "descripcion"),
        image_urls=_string_list(payload.get("fotos")),
        published_at=_parse_date(_optional_str(payload, "publicado")),
    )


def _optional_str(payload: Mapping[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(payload: Mapping[str, Any], key: str) -> int | None:
    value = payload.get(key)
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise NormalizationError(f"invalid integer for {key}: {value!r}") from exc


def _require_int(payload: Mapping[str, Any], key: str) -> int:
    value = _optional_int(payload, key)
    if value is None:
        raise NormalizationError(f"missing required field: {key}")
    return value


def _require_decimal(payload: Mapping[str, Any], key: str) -> Decimal:
    value = payload.get(key)
    if value is None or value == "":
        raise NormalizationError(f"missing required field: {key}")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise NormalizationError(f"invalid number for {key}: {value!r}") from exc


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item) for item in value if item is not None]


def _parse_date(value: str | None) -> datetime | None:
    if value is None:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None
