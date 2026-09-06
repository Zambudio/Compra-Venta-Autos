"""Consultas de anuncios: filtrado, ordenación y paginación."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import ColumnElement, Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.listings.models import VehicleListing
from app.search.schemas import SearchFilter, SortOrder
from app.sources.models import Source


class ListingRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def search(
        self, criteria: SearchFilter
    ) -> tuple[Sequence[tuple[VehicleListing, str]], int]:
        base = select(VehicleListing, Source.key).join(
            Source, Source.id == VehicleListing.source_id
        )
        base = _apply_filters(base, criteria)

        total = await self.db.scalar(
            select(func.count()).select_from(base.order_by(None).subquery())
        )
        rows = base.order_by(*_order_by(criteria.sort))
        rows = rows.limit(criteria.page_size).offset((criteria.page - 1) * criteria.page_size)
        result = await self.db.execute(rows)
        return list(result.tuples().all()), int(total or 0)

    async def get_with_snapshots(self, listing_id: UUID) -> tuple[VehicleListing, str] | None:
        result = await self.db.execute(
            select(VehicleListing, Source.key)
            .join(Source, Source.id == VehicleListing.source_id)
            .where(VehicleListing.id == listing_id)
            .options(selectinload(VehicleListing.snapshots))
        )
        row = result.tuples().one_or_none()
        return row


def _apply_filters(
    stmt: Select[tuple[VehicleListing, str]], f: SearchFilter
) -> Select[tuple[VehicleListing, str]]:
    if f.brand:
        stmt = stmt.where(func.lower(VehicleListing.brand) == f.brand.lower())
    if f.model:
        stmt = stmt.where(VehicleListing.model.ilike(f"%{f.model}%"))
    if f.year_min is not None:
        stmt = stmt.where(VehicleListing.year >= f.year_min)
    if f.year_max is not None:
        stmt = stmt.where(VehicleListing.year <= f.year_max)
    if f.price_min is not None:
        stmt = stmt.where(VehicleListing.price_amount >= f.price_min)
    if f.price_max is not None:
        stmt = stmt.where(VehicleListing.price_amount <= f.price_max)
    if f.fuel_type is not None:
        stmt = stmt.where(VehicleListing.fuel_type == f.fuel_type)
    if f.mileage_max is not None:
        stmt = stmt.where(VehicleListing.mileage_km <= f.mileage_max)
    if f.province:
        stmt = stmt.where(func.lower(VehicleListing.province) == f.province.lower())
    if f.seller_type is not None:
        stmt = stmt.where(VehicleListing.seller_type == f.seller_type)
    if f.status is not None:
        stmt = stmt.where(VehicleListing.status == f.status)
    if f.source:
        stmt = stmt.where(Source.key.in_(f.source))
    return stmt


def _order_by(sort: SortOrder) -> tuple[ColumnElement[Any], ColumnElement[Any]]:
    if sort is SortOrder.PRICE_ASC:
        return (VehicleListing.price_amount.asc(), VehicleListing.id.asc())
    if sort is SortOrder.PRICE_DESC:
        return (VehicleListing.price_amount.desc(), VehicleListing.id.asc())
    return (VehicleListing.first_seen_at.desc(), VehicleListing.id.asc())
