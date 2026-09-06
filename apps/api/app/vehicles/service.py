"""Servicio de gestión de vehículos, matching asistido y deduplicación."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.models import AuditEvent
from app.listings.models import VehicleListing
from app.listings.vocab import ListingStatus
from app.vehicles.errors import (
    MatchCandidateAlreadyDecidedError,
    MatchCandidateNotFoundError,
    VehicleNotFoundError,
)
from app.vehicles.history import calculate_vehicle_history
from app.vehicles.market import estimate_market_price
from app.vehicles.matching import score_match
from app.vehicles.models import MarketEstimate, Vehicle, VehicleMatchCandidate
from app.vehicles.schemas import VehicleHistoryMetrics
from app.vehicles.vocab import MatchCandidateStatus


class VehicleService:
    @staticmethod
    async def generate_match_candidates(
        session: AsyncSession,
        new_listing_ids: Sequence[UUID] | None = None,
        min_confidence: Decimal = Decimal("0.600"),
    ) -> int:
        """Busca pares potenciales y genera candidatos en estado PENDING si superan el umbral."""
        stmt = select(VehicleListing)
        if new_listing_ids is not None:
            stmt = stmt.where(VehicleListing.id.in_(new_listing_ids))
        target_listings = (await session.execute(stmt)).scalars().all()

        if not target_listings:
            return 0

        created_count = 0
        all_active_stmt = select(VehicleListing)
        all_active = (await session.execute(all_active_stmt)).scalars().all()

        for target in target_listings:
            for other in all_active:
                if target.id == other.id:
                    continue
                # Si ambos ya pertenecen al mismo vehículo, no tiene sentido sugerirlo
                if target.vehicle_id is not None and target.vehicle_id == other.vehicle_id:
                    continue

                min_id, max_id = (
                    (target.id, other.id) if target.id < other.id else (other.id, target.id)
                )

                # Verificar si ya existe candidato para este par ordenado
                existing_stmt = select(VehicleMatchCandidate.id).where(
                    VehicleMatchCandidate.listing_a_id == min_id,
                    VehicleMatchCandidate.listing_b_id == max_id,
                )
                existing = (await session.execute(existing_stmt)).scalar_one_or_none()
                if existing is not None:
                    continue

                l_a = target if target.id == min_id else other
                l_b = other if target.id == min_id else target

                dict_a = {
                    "id": l_a.id,
                    "brand": l_a.brand,
                    "model": l_a.model,
                    "year": l_a.year,
                    "mileage_km": l_a.mileage_km,
                    "price_amount": l_a.price_amount,
                    "fuel_type": l_a.fuel_type,
                    "transmission": l_a.transmission,
                    "province": l_a.province,
                    "trim": l_a.trim,
                    "description": l_a.description,
                }
                dict_b = {
                    "id": l_b.id,
                    "brand": l_b.brand,
                    "model": l_b.model,
                    "year": l_b.year,
                    "mileage_km": l_b.mileage_km,
                    "price_amount": l_b.price_amount,
                    "fuel_type": l_b.fuel_type,
                    "transmission": l_b.transmission,
                    "province": l_b.province,
                    "trim": l_b.trim,
                    "description": l_b.description,
                }

                result = score_match(dict_a, dict_b)
                if result.confidence >= min_confidence:
                    candidate = VehicleMatchCandidate(
                        listing_a_id=min_id,
                        listing_b_id=max_id,
                        confidence_score=result.confidence,
                        match_reasons=result.reasons,
                        status=MatchCandidateStatus.PENDING,
                    )
                    session.add(candidate)
                    created_count += 1

        if created_count > 0:
            await session.flush()

        return created_count

    @staticmethod
    async def list_match_candidates(
        session: AsyncSession,
        status: MatchCandidateStatus | None = MatchCandidateStatus.PENDING,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[VehicleMatchCandidate], int]:
        stmt = select(VehicleMatchCandidate).options(
            selectinload(VehicleMatchCandidate.listing_a),
            selectinload(VehicleMatchCandidate.listing_b),
        )
        if status is not None:
            stmt = stmt.where(VehicleMatchCandidate.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        offset = (page - 1) * page_size
        stmt = (
            stmt.order_by(
                VehicleMatchCandidate.confidence_score.desc(),
                VehicleMatchCandidate.created_at.desc(),
            )
            .offset(offset)
            .limit(page_size)
        )

        items = list((await session.execute(stmt)).scalars().all())
        return items, total

    @staticmethod
    async def confirm_match(
        session: AsyncSession,
        candidate_id: UUID,
        user_id: UUID,
    ) -> VehicleMatchCandidate:
        stmt = (
            select(VehicleMatchCandidate)
            .where(VehicleMatchCandidate.id == candidate_id)
            .options(
                selectinload(VehicleMatchCandidate.listing_a),
                selectinload(VehicleMatchCandidate.listing_b),
            )
        )
        candidate = (await session.execute(stmt)).scalar_one_or_none()
        if candidate is None:
            raise MatchCandidateNotFoundError(candidate_id)

        if candidate.status != MatchCandidateStatus.PENDING:
            raise MatchCandidateAlreadyDecidedError(candidate_id, candidate.status.value)

        l_a = candidate.listing_a
        l_b = candidate.listing_b

        vehicle_id: UUID
        if l_a.vehicle_id is None and l_b.vehicle_id is None:
            first_listed = datetime.now(UTC)
            if l_a.first_seen_at and l_b.first_seen_at:
                first_listed = min(l_a.first_seen_at, l_b.first_seen_at)
            elif l_a.first_seen_at:
                first_listed = l_a.first_seen_at
            elif l_b.first_seen_at:
                first_listed = l_b.first_seen_at

            new_vehicle = Vehicle(
                id=uuid4(),
                brand=l_a.brand,
                model=l_a.model,
                generation=l_a.generation or l_b.generation,
                trim=l_a.trim or l_b.trim,
                engine_code=l_a.engine_code or l_b.engine_code,
                power_kw=l_a.power_kw or l_b.power_kw,
                fuel_type=l_a.fuel_type,
                transmission=l_a.transmission,
                year=min(l_a.year, l_b.year),
                first_listed_at=first_listed,
                listing_count=2,
            )
            session.add(new_vehicle)
            await session.flush()
            l_a.vehicle_id = new_vehicle.id
            l_b.vehicle_id = new_vehicle.id
            vehicle_id = new_vehicle.id
        elif l_a.vehicle_id is not None and l_b.vehicle_id is None:
            l_b.vehicle_id = l_a.vehicle_id
            v = await session.get(Vehicle, l_a.vehicle_id)
            if v:
                v.listing_count += 1
            vehicle_id = l_a.vehicle_id
        elif l_a.vehicle_id is None and l_b.vehicle_id is not None:
            l_a.vehicle_id = l_b.vehicle_id
            v = await session.get(Vehicle, l_b.vehicle_id)
            if v:
                v.listing_count += 1
            vehicle_id = l_b.vehicle_id
        else:
            # Ambos ya tenían un vehículo asignado distinto: unificar en el primero
            assert l_a.vehicle_id is not None
            assert l_b.vehicle_id is not None
            primary_v_id = l_a.vehicle_id
            secondary_v_id = l_b.vehicle_id
            if primary_v_id != secondary_v_id:
                # Reasignar todos los listings del vehículo secundario al primario
                reassign_stmt = select(VehicleListing).where(
                    VehicleListing.vehicle_id == secondary_v_id
                )
                sec_listings = (await session.execute(reassign_stmt)).scalars().all()
                primary_v = await session.get(Vehicle, primary_v_id)
                sec_v = await session.get(Vehicle, secondary_v_id)
                for item in sec_listings:
                    item.vehicle_id = primary_v_id
                if primary_v and sec_v:
                    primary_v.listing_count += sec_v.listing_count
                    await session.delete(sec_v)
            vehicle_id = primary_v_id

        candidate.status = MatchCandidateStatus.CONFIRMED
        candidate.decided_by_user_id = user_id
        candidate.decided_at = datetime.now(UTC)

        audit = AuditEvent(
            actor_user_id=user_id,
            action="manual_match",
            entity_type="vehicle_match_candidate",
            entity_id=str(candidate.id),
            request_id="internal",
            result="success",
            event_metadata={
                "vehicle_id": str(vehicle_id),
                "listing_a_id": str(candidate.listing_a_id),
                "listing_b_id": str(candidate.listing_b_id),
                "confidence_score": str(candidate.confidence_score),
            },
        )
        session.add(audit)
        await session.flush()
        return candidate

    @staticmethod
    async def reject_match(
        session: AsyncSession,
        candidate_id: UUID,
        user_id: UUID,
    ) -> VehicleMatchCandidate:
        stmt = select(VehicleMatchCandidate).where(VehicleMatchCandidate.id == candidate_id)
        candidate = (await session.execute(stmt)).scalar_one_or_none()
        if candidate is None:
            raise MatchCandidateNotFoundError(candidate_id)

        if candidate.status != MatchCandidateStatus.PENDING:
            raise MatchCandidateAlreadyDecidedError(candidate_id, candidate.status.value)

        candidate.status = MatchCandidateStatus.REJECTED
        candidate.decided_by_user_id = user_id
        candidate.decided_at = datetime.now(UTC)

        audit = AuditEvent(
            actor_user_id=user_id,
            action="manual_match_rejected",
            entity_type="vehicle_match_candidate",
            entity_id=str(candidate.id),
            request_id="internal",
            result="success",
            event_metadata={
                "listing_a_id": str(candidate.listing_a_id),
                "listing_b_id": str(candidate.listing_b_id),
            },
        )
        session.add(audit)
        await session.flush()
        return candidate

    @staticmethod
    async def get_vehicle(
        session: AsyncSession,
        vehicle_id: UUID,
    ) -> Vehicle | None:
        stmt = (
            select(Vehicle)
            .where(Vehicle.id == vehicle_id)
            .options(
                selectinload(Vehicle.listings).selectinload(VehicleListing.snapshots),
                selectinload(Vehicle.estimates),
            )
        )
        return (await session.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def list_vehicles(
        session: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        brand: str | None = None,
        model: str | None = None,
    ) -> tuple[list[Vehicle], int]:
        stmt = select(Vehicle)
        if brand:
            stmt = stmt.where(Vehicle.brand.ilike(f"%{brand}%"))
        if model:
            stmt = stmt.where(Vehicle.model.ilike(f"%{model}%"))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        offset = (page - 1) * page_size
        stmt = stmt.order_by(Vehicle.created_at.desc()).offset(offset).limit(page_size)

        items = list((await session.execute(stmt)).scalars().all())
        return items, total

    @staticmethod
    async def get_vehicle_detail(
        session: AsyncSession,
        vehicle_id: UUID,
    ) -> Vehicle:
        vehicle = await VehicleService.get_vehicle(session, vehicle_id)
        if vehicle is None:
            raise VehicleNotFoundError(vehicle_id)
        return vehicle

    @staticmethod
    async def get_vehicle_history(
        session: AsyncSession,
        vehicle_id: UUID,
    ) -> VehicleHistoryMetrics:
        vehicle = await VehicleService.get_vehicle_detail(session, vehicle_id)
        snaps_list = [
            listing_item.snapshots for listing_item in vehicle.listings if listing_item.snapshots
        ]
        current_prices = [
            listing_item.price_amount
            for listing_item in vehicle.listings
            if listing_item.price_amount is not None
        ]
        return calculate_vehicle_history(snaps_list, current_prices)

    @staticmethod
    async def compute_and_save_market_estimate(
        session: AsyncSession,
        vehicle_id: UUID,
        min_comparables: int = 3,
    ) -> MarketEstimate:
        vehicle = await VehicleService.get_vehicle_detail(session, vehicle_id)
        pool_stmt = select(VehicleListing).where(
            VehicleListing.brand.ilike(vehicle.brand),
            VehicleListing.model.ilike(vehicle.model),
            VehicleListing.status == ListingStatus.ACTIVE,
        )
        pool = list((await session.execute(pool_stmt)).scalars().all())

        target_dict = {
            "id": vehicle.id,
            "brand": vehicle.brand,
            "model": vehicle.model,
            "year": vehicle.year,
            "mileage_km": vehicle.listings[0].mileage_km if vehicle.listings else None,
            "price_amount": vehicle.listings[0].price_amount if vehicle.listings else None,
            "fuel_type": vehicle.fuel_type,
            "transmission": vehicle.transmission,
            "trim": vehicle.trim,
        }

        pool_dicts = [
            {
                "id": item.id,
                "brand": item.brand,
                "model": item.model,
                "year": item.year,
                "mileage_km": item.mileage_km,
                "price_amount": item.price_amount,
                "fuel_type": item.fuel_type,
                "transmission": item.transmission,
                "trim": item.trim,
            }
            for item in pool
            if item.vehicle_id != vehicle.id
        ]

        calc_result = estimate_market_price(target_dict, pool_dicts)

        now = datetime.now(UTC)
        estimate = MarketEstimate(
            id=uuid4(),
            vehicle_id=vehicle.id,
            estimated_amount=calc_result.estimated_amount,
            low_amount=calc_result.low_amount,
            high_amount=calc_result.high_amount,
            currency=calc_result.currency,
            method=calc_result.method,
            number_of_comparables=calc_result.number_of_comparables,
            confidence_score=calc_result.confidence_score,
            calculated_at=now,
        )
        session.add(estimate)
        await session.flush()
        return estimate
