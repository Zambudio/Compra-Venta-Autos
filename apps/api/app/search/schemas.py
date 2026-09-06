"""Filtro de búsqueda de la API (Plan Maestro §10, extensible).

Es un superconjunto del `ConnectorSearchFilter`: incluye además ordenación,
`status` y selección de fuentes, que aplican sobre los anuncios ya persistidos.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.connectors.filters import ConnectorSearchFilter
from app.listings.vocab import FuelType, ListingStatus, SellerType

_MAX_PAGE_SIZE = 100


class SortOrder(StrEnum):
    NEWEST = "newest"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"


class SearchFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brand: str | None = None
    model: str | None = None
    year_min: int | None = Field(default=None, ge=1950, le=2100)
    year_max: int | None = Field(default=None, ge=1950, le=2100)
    price_min: Decimal | None = Field(default=None, ge=0)
    price_max: Decimal | None = Field(default=None, ge=0)
    fuel_type: FuelType | None = None
    mileage_max: int | None = Field(default=None, ge=0)
    province: str | None = None
    seller_type: SellerType | None = None
    source: list[str] = Field(default_factory=list)
    status: ListingStatus | None = None
    sort: SortOrder = SortOrder.NEWEST
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=_MAX_PAGE_SIZE)

    @model_validator(mode="after")
    def _check_ranges(self) -> SearchFilter:
        if (
            self.year_min is not None
            and self.year_max is not None
            and self.year_min > self.year_max
        ):
            raise ValueError("year_min must not exceed year_max")
        if (
            self.price_min is not None
            and self.price_max is not None
            and self.price_min > self.price_max
        ):
            raise ValueError("price_min must not exceed price_max")
        return self

    def to_connector_filter(self, *, page: int, page_size: int) -> ConnectorSearchFilter:
        return ConnectorSearchFilter(
            brand=self.brand,
            model=self.model,
            year_min=self.year_min,
            year_max=self.year_max,
            price_min=self.price_min,
            price_max=self.price_max,
            fuel_type=self.fuel_type,
            mileage_max=self.mileage_max,
            province=self.province,
            seller_type=self.seller_type,
            page=page,
            page_size=page_size,
        )
