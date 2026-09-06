"""Filtro que un conector entiende.

Es un subconjunto de `SearchFilter` del Plan Maestro §10: la capa API traduce la
petición del usuario a este objeto antes de llamar al conector.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.listings.vocab import FuelType, SellerType


@dataclass(frozen=True, slots=True)
class ConnectorSearchFilter:
    brand: str | None = None
    model: str | None = None
    year_min: int | None = None
    year_max: int | None = None
    price_min: Decimal | None = None
    price_max: Decimal | None = None
    fuel_type: FuelType | None = None
    mileage_max: int | None = None
    province: str | None = None
    seller_type: SellerType | None = None
    page: int = 1
    page_size: int = 20
