"""Ingesta de anuncios: normaliza, deduplica y persiste de forma trazable.

Reglas (ADR-0012):
- un anuncio es `(source_id, external_id)`;
- si el `payload_hash` ya está almacenado para ese anuncio, solo se refresca
  `last_seen_at`;
- si el payload es nuevo, se actualiza el anuncio y se añade un `ListingSnapshot`
  cuando cambia precio, kilometraje o el hash de la descripción;
- `RawListingPayload` es inmutable.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.manual import ManualEntryConnector
from app.connectors.schemas import RawListing
from app.listings.models import ListingSnapshot, RawListingPayload, VehicleListing
from app.listings.normalizer import NormalizedListing, normalize, payload_hash
from app.listings.repository import ListingRepository
from app.listings.schemas import (
    ListingDetailRead,
    ListingPage,
    ListingRead,
    ManualListingCreate,
    SnapshotRead,
)
from app.listings.vocab import EntryChannel, ListingStatus, ProviderKind
from app.search.schemas import SearchFilter
from app.sources.models import Source


class ListingNotFoundError(Exception):
    def __init__(self, listing_id: UUID) -> None:
        super().__init__(f"unknown listing: {listing_id}")
        self.listing_id = listing_id


class DuplicateManualListingError(Exception):
    def __init__(self, listing_id: UUID) -> None:
        super().__init__("this vehicle was already registered manually")
        self.listing_id = listing_id


_ENTRY_CHANNEL_BY_PROVIDER = {
    ProviderKind.MOCK: EntryChannel.MOCK_SYNC,
    ProviderKind.MANUAL: EntryChannel.MANUAL_ENTRY,
    ProviderKind.CONNECTOR: EntryChannel.MOCK_SYNC,
}


@dataclass(frozen=True, slots=True)
class IngestDecision:
    action: Literal["create", "update", "seen"]
    write_snapshot: bool


@dataclass(frozen=True, slots=True)
class IngestOutcome:
    listing_id: UUID
    created: bool
    updated: bool
    snapshot_created: bool


def decide_ingest(
    *,
    listing_exists: bool,
    payload_already_seen: bool,
    existing_price: Decimal | None,
    existing_mileage: int | None,
    existing_description_hash: str | None,
    new_price: Decimal,
    new_mileage: int,
    new_description_hash: str | None,
) -> IngestDecision:
    if not listing_exists:
        return IngestDecision(action="create", write_snapshot=True)
    if payload_already_seen:
        return IngestDecision(action="seen", write_snapshot=False)
    changed = (
        existing_price != new_price
        or existing_mileage != new_mileage
        or existing_description_hash != new_description_hash
    )
    return IngestDecision(action="update", write_snapshot=changed)


def description_hash(description: str | None) -> str | None:
    if description is None:
        return None
    return hashlib.sha256(description.encode("utf-8")).hexdigest()


class ListingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repository = ListingRepository(db)

    async def search(self, criteria: SearchFilter) -> ListingPage:
        rows, total = await self.repository.search(criteria)
        return ListingPage(
            items=[_listing_read(listing, source_key) for listing, source_key in rows],
            page=criteria.page,
            page_size=criteria.page_size,
            total=total,
            has_more=criteria.page * criteria.page_size < total,
        )

    async def get_detail(self, listing_id: UUID) -> ListingDetailRead:
        row = await self.repository.get_with_snapshots(listing_id)
        if row is None:
            raise ListingNotFoundError(listing_id)
        listing, source_key = row
        return ListingDetailRead(
            **_listing_read(listing, source_key).model_dump(),
            snapshots=[SnapshotRead.model_validate(snap) for snap in listing.snapshots],
        )

    async def create_manual(self, data: ManualListingCreate) -> ListingRead:
        source = (await self.db.execute(select(Source).where(Source.key == "manual"))).scalar_one()
        observed = _manual_observed_payload(data)
        raw = ManualEntryConnector().build_raw(observed)
        outcome = await self.ingest_raw(raw, source)
        if not outcome.created:
            raise DuplicateManualListingError(outcome.listing_id)
        await self.db.flush()
        row = await self.repository.get_with_snapshots(outcome.listing_id)
        assert row is not None
        listing, source_key = row
        return _listing_read(listing, source_key)

    async def ingest_raw(self, raw: RawListing, source: Source) -> IngestOutcome:
        normalized = normalize(raw.payload, raw.source_key)
        phash = payload_hash(raw.payload)
        observed_at = _as_utc(raw.retrieved_at)

        existing = await self._get_listing(source.id, raw.external_id)
        payload_already_seen = existing is not None and await self._payload_seen(existing.id, phash)
        new_description_hash = description_hash(normalized.description)

        decision = decide_ingest(
            listing_exists=existing is not None,
            payload_already_seen=payload_already_seen,
            existing_price=existing.price_amount if existing else None,
            existing_mileage=existing.mileage_km if existing else None,
            existing_description_hash=_last_description_hash(existing),
            new_price=normalized.price_amount,
            new_mileage=normalized.mileage_km,
            new_description_hash=new_description_hash,
        )

        if decision.action == "create":
            return await self._create(raw, source, normalized, phash, observed_at)

        assert existing is not None
        if decision.action == "seen":
            existing.last_seen_at = max(existing.last_seen_at, observed_at)
            return IngestOutcome(existing.id, created=False, updated=False, snapshot_created=False)

        return await self._update(
            existing, raw, source, normalized, phash, observed_at, decision.write_snapshot
        )

    async def _create(
        self,
        raw: RawListing,
        source: Source,
        normalized: NormalizedListing,
        phash: str,
        observed_at: datetime,
    ) -> IngestOutcome:
        listing = VehicleListing(
            source_id=source.id,
            external_id=raw.external_id,
            entry_channel=_ENTRY_CHANNEL_BY_PROVIDER[source.provider_kind],
            status=ListingStatus.ACTIVE,
            payload_hash=phash,
            first_seen_at=observed_at,
            last_seen_at=observed_at,
            **_listing_fields(normalized),
        )
        self.db.add(listing)
        await self.db.flush()
        self.db.add(_raw_payload(listing.id, raw, source, phash, observed_at))
        self.db.add(_snapshot(listing.id, normalized, observed_at))
        return IngestOutcome(listing.id, created=True, updated=False, snapshot_created=True)

    async def _update(
        self,
        listing: VehicleListing,
        raw: RawListing,
        source: Source,
        normalized: NormalizedListing,
        phash: str,
        observed_at: datetime,
        write_snapshot: bool,
    ) -> IngestOutcome:
        for field, value in _listing_fields(normalized).items():
            setattr(listing, field, value)
        listing.payload_hash = phash
        listing.last_seen_at = observed_at
        self.db.add(_raw_payload(listing.id, raw, source, phash, observed_at))
        if write_snapshot:
            self.db.add(_snapshot(listing.id, normalized, observed_at))
        return IngestOutcome(
            listing.id, created=False, updated=True, snapshot_created=write_snapshot
        )

    async def _get_listing(self, source_id: UUID, external_id: str) -> VehicleListing | None:
        result = await self.db.execute(
            select(VehicleListing).where(
                VehicleListing.source_id == source_id,
                VehicleListing.external_id == external_id,
            )
        )
        return result.scalar_one_or_none()

    async def _payload_seen(self, listing_id: UUID, phash: str) -> bool:
        result = await self.db.execute(
            select(RawListingPayload.id).where(
                RawListingPayload.listing_id == listing_id,
                RawListingPayload.payload_hash == phash,
            )
        )
        return result.first() is not None


def _listing_fields(n: NormalizedListing) -> dict[str, object]:
    return {
        "url": n.url,
        "brand": n.brand,
        "model": n.model,
        "generation": n.generation,
        "trim": n.trim,
        "engine_code": n.engine_code,
        "power_kw": n.power_kw,
        "fuel_type": n.fuel_type,
        "transmission": n.transmission,
        "year": n.year,
        "mileage_km": n.mileage_km,
        "price_amount": n.price_amount,
        "price_currency": n.price_currency,
        "location": n.location,
        "province": n.province,
        "seller_type": n.seller_type,
        "description": n.description,
        "image_urls": list(n.image_urls),
        "published_at": _as_utc(n.published_at) if n.published_at else None,
    }


def _raw_payload(
    listing_id: UUID, raw: RawListing, source: Source, phash: str, observed_at: datetime
) -> RawListingPayload:
    return RawListingPayload(
        listing_id=listing_id,
        source_id=source.id,
        external_id=raw.external_id,
        payload=dict(raw.payload),
        payload_hash=phash,
        connector_version=raw.connector_version,
        retrieved_at=observed_at,
    )


def _snapshot(
    listing_id: UUID, normalized: NormalizedListing, observed_at: datetime
) -> ListingSnapshot:
    return ListingSnapshot(
        listing_id=listing_id,
        observed_at=observed_at,
        price_amount=normalized.price_amount,
        price_currency=normalized.price_currency,
        mileage_km=normalized.mileage_km,
        status=ListingStatus.ACTIVE,
        description_hash=description_hash(normalized.description),
    )


def _last_description_hash(listing: VehicleListing | None) -> str | None:
    if listing is None:
        return None
    return description_hash(listing.description)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _listing_read(listing: VehicleListing, source_key: str) -> ListingRead:
    return ListingRead(
        id=listing.id,
        source_key=source_key,
        external_id=listing.external_id,
        url=listing.url,
        brand=listing.brand,
        model=listing.model,
        generation=listing.generation,
        trim=listing.trim,
        engine_code=listing.engine_code,
        power_kw=listing.power_kw,
        fuel_type=listing.fuel_type,
        transmission=listing.transmission,
        year=listing.year,
        mileage_km=listing.mileage_km,
        price_amount=listing.price_amount,
        price_currency=listing.price_currency,
        location=listing.location,
        province=listing.province,
        seller_type=listing.seller_type,
        description=listing.description,
        image_urls=list(listing.image_urls),
        status=listing.status,
        first_seen_at=listing.first_seen_at,
        last_seen_at=listing.last_seen_at,
        published_at=listing.published_at,
    )


def _manual_external_id(data: ManualListingCreate) -> str:
    seed = f"{data.brand}|{data.model}|{data.year}|{data.mileage_km}|{data.url or ''}".casefold()
    return "manual-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]


def _manual_observed_payload(data: ManualListingCreate) -> dict[str, object]:
    return {
        "external_id": _manual_external_id(data),
        "url": data.url,
        "marca": data.brand,
        "modelo": data.model,
        "version": data.trim,
        "generacion": data.generation,
        "codigo_motor": data.engine_code,
        "anio": data.year,
        "km": data.mileage_km,
        "precio": str(data.price_amount),
        "moneda": "EUR",
        "combustible": data.fuel_type.value,
        "cambio": data.transmission.value,
        "vendedor": data.seller_type.value,
        "provincia": data.province,
        "poblacion": data.location,
        "descripcion": data.description,
        "fotos": list(data.image_urls),
    }
