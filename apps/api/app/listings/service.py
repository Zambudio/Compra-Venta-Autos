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

from app.connectors.schemas import RawListing
from app.listings.models import ListingSnapshot, RawListingPayload, VehicleListing
from app.listings.normalizer import NormalizedListing, normalize, payload_hash
from app.listings.vocab import EntryChannel, ListingStatus, ProviderKind
from app.sources.models import Source

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
