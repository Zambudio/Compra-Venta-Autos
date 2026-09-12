"""Servicio de dominio para perfiles de scoring, evaluación determinista y oportunidades."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.knowledge.models import VehicleMitigation
from app.knowledge.service import KnowledgeService
from app.listings.models import VehicleListing
from app.scoring.engine import evaluate_opportunity_score
from app.scoring.errors import (
    OpportunityNotFoundError,
    ScoringProfileNotFoundError,
    ScoringProfileSlugAlreadyExistsError,
    ScoringProfileVersionNotFoundError,
    TargetNotFoundError,
)
from app.scoring.models import (
    Opportunity,
    OpportunityScore,
    ScoringProfile,
    ScoringProfileVersion,
)
from app.scoring.schemas import (
    OpportunityRead,
    ScoringProfileCreate,
    ScoringProfileVersionCreate,
)
from app.scoring.valuation import compute_economic_valuation, compute_seller_pressure
from app.scoring.vocab import (
    DEFAULT_SCORING_WEIGHTS,
    OpportunityStatus,
    SellerPressureLevel,
)
from app.vehicles.models import MarketEstimate, Vehicle

DEFAULT_PROFILE_SLUG = "reventa-rapida"


class ScoringService:
    @staticmethod
    async def get_or_create_default_profile(
        session: AsyncSession,
    ) -> tuple[ScoringProfile, ScoringProfileVersion]:
        """Obtiene o crea el perfil por defecto 'reventa-rapida' con versión inmutable 1."""
        stmt = (
            select(ScoringProfile)
            .options(selectinload(ScoringProfile.versions))
            .where(ScoringProfile.slug == DEFAULT_PROFILE_SLUG)
        )
        profile = (await session.execute(stmt)).scalar_one_or_none()

        if profile and profile.versions:
            sorted_versions = sorted(profile.versions, key=lambda v: v.version_number, reverse=True)
            return profile, sorted_versions[0]

        if not profile:
            profile = ScoringProfile(
                id=uuid4(),
                name="Oportunidad Reventa Rápida",
                slug=DEFAULT_PROFILE_SLUG,
                description=(
                    "Perfil estándar para vehículos populares de hasta 3.000 € (Plan Maestro §18)."
                ),
                is_active=True,
            )
            session.add(profile)
            await session.flush()

        version = ScoringProfileVersion(
            id=uuid4(),
            profile_id=profile.id,
            version_number=1,
            weights=dict(DEFAULT_SCORING_WEIGHTS),
            config={
                "fast_sale_discount_ratio": 0.88,
                "preparation_cost_default": 200.0,
                "transfer_tax_ratio": 0.04,
                "transfer_fee_dgt": 55.70,
                "target_roi_min": 25.0,
            },
            is_immutable=True,
        )
        session.add(version)
        await session.flush()
        await session.refresh(profile, ["versions"])
        return profile, version

    @staticmethod
    async def list_profiles(session: AsyncSession) -> Sequence[ScoringProfile]:
        stmt = (
            select(ScoringProfile)
            .options(selectinload(ScoringProfile.versions))
            .order_by(ScoringProfile.created_at.asc())
        )
        return (await session.execute(stmt)).scalars().all()

    @staticmethod
    async def get_profile(session: AsyncSession, profile_id: UUID) -> ScoringProfile:
        stmt = (
            select(ScoringProfile)
            .options(selectinload(ScoringProfile.versions))
            .where(ScoringProfile.id == profile_id)
        )
        profile = (await session.execute(stmt)).scalar_one_or_none()
        if not profile:
            raise ScoringProfileNotFoundError(profile_id)
        return profile

    @staticmethod
    async def create_profile(
        session: AsyncSession,
        data: ScoringProfileCreate,
    ) -> ScoringProfile:
        stmt = select(ScoringProfile).where(ScoringProfile.slug == data.slug)
        if (await session.execute(stmt)).scalar_one_or_none():
            raise ScoringProfileSlugAlreadyExistsError(data.slug)

        profile = ScoringProfile(
            name=data.name,
            slug=data.slug,
            description=data.description,
            is_active=True,
        )
        session.add(profile)
        await session.flush()

        version = ScoringProfileVersion(
            profile_id=profile.id,
            version_number=1,
            weights=data.initial_weights,
            config=data.initial_config,
            is_immutable=True,
        )
        session.add(version)
        await session.flush()
        await session.refresh(profile, ["versions"])
        return profile

    @staticmethod
    async def create_profile_version(
        session: AsyncSession,
        profile_id: UUID,
        data: ScoringProfileVersionCreate,
    ) -> ScoringProfileVersion:
        profile = await ScoringService.get_profile(session, profile_id)
        max_v = max([v.version_number for v in profile.versions], default=0)

        new_version = ScoringProfileVersion(
            profile_id=profile.id,
            version_number=max_v + 1,
            weights=data.weights,
            config=data.config,
            is_immutable=True,
        )
        session.add(new_version)
        await session.flush()
        return new_version

    @staticmethod
    async def get_profile_version(
        session: AsyncSession,
        version_id: UUID,
    ) -> ScoringProfileVersion:
        stmt = (
            select(ScoringProfileVersion)
            .options(selectinload(ScoringProfileVersion.profile))
            .where(ScoringProfileVersion.id == version_id)
        )
        version = (await session.execute(stmt)).scalar_one_or_none()
        if not version:
            raise ScoringProfileVersionNotFoundError(version_id)
        return version

    # --- Evaluación de Oportunidades ---

    @staticmethod
    async def evaluate_listing(
        session: AsyncSession,
        listing_id: UUID,
        profile_version_id: UUID | None = None,
    ) -> Opportunity:
        """Evalúa un anuncio individual generando su OpportunityScore y su Opportunity."""
        # 1. Cargar listing con snapshots
        stmt = (
            select(VehicleListing)
            .options(
                selectinload(VehicleListing.snapshots),
                selectinload(VehicleListing.vehicle),
            )
            .where(VehicleListing.id == listing_id)
        )
        listing = (await session.execute(stmt)).scalar_one_or_none()
        if not listing:
            raise TargetNotFoundError("anuncio", listing_id)

        # 2. Obtener versión de perfil
        if profile_version_id:
            version = await ScoringService.get_profile_version(session, profile_version_id)
        else:
            _, version = await ScoringService.get_or_create_default_profile(session)

        # 3. Datos de mercado
        vehicle_id = listing.vehicle_id
        market_estimate: MarketEstimate | None = None
        if vehicle_id:
            m_stmt = (
                select(MarketEstimate)
                .where(MarketEstimate.vehicle_id == vehicle_id)
                .order_by(MarketEstimate.calculated_at.desc())
                .limit(1)
            )
            market_estimate = (await session.execute(m_stmt)).scalar_one_or_none()
        if not market_estimate:
            m_stmt = (
                select(MarketEstimate)
                .where(MarketEstimate.listing_id == listing_id)
                .order_by(MarketEstimate.calculated_at.desc())
                .limit(1)
            )
            market_estimate = (await session.execute(m_stmt)).scalar_one_or_none()

        # 4. Knowledge Base: diagnóstico y riesgos
        fuel_str = (
            listing.fuel_type.value
            if hasattr(listing.fuel_type, "value")
            else str(listing.fuel_type)
        )
        kb_diag = await KnowledgeService.lookup_vehicle_reliability(
            session=session,
            brand=listing.brand,
            model=listing.model,
            year=listing.year,
            fuel_type=fuel_str,
            engine_code=None,
        )

        # Mitigaciones documentadas
        mitigations_count = 0
        if vehicle_id:
            mit_stmt = select(func.count(VehicleMitigation.id)).where(
                VehicleMitigation.vehicle_id == vehicle_id
            )
            mitigations_count = (await session.execute(mit_stmt)).scalar_one() or 0

        # 5. Presión del vendedor
        (
            pressure_level,
            pressure_reasons,
            days_on_market,
            reductions_count,
            _red_amount,
            _red_pct,
        ) = compute_seller_pressure(
            published_at=listing.published_at,
            last_seen_at=listing.last_seen_at,
            snapshots=listing.snapshots,
            current_price=listing.price_amount,
        )

        # 6. Valoración económica
        valuation = compute_economic_valuation(
            asking_price=listing.price_amount,
            estimated_market_price=(market_estimate.estimated_amount if market_estimate else None),
            market_estimate_low=(market_estimate.low_amount if market_estimate else None),
            market_estimate_high=(market_estimate.high_amount if market_estimate else None),
            number_of_comparables=(market_estimate.number_of_comparables if market_estimate else 0),
            market_confidence_score=(
                market_estimate.confidence_score if market_estimate else Decimal("0.00")
            ),
            known_issues_repair_min=kb_diag.total_estimated_repair_min,
            known_issues_repair_max=kb_diag.total_estimated_repair_max,
            config=version.config,
        )

        # 7. Motor de scoring determinista (9 componentes)
        eval_result = evaluate_opportunity_score(
            weights=version.weights,
            asking_price=listing.price_amount,
            market_median=market_estimate.estimated_amount if market_estimate else None,
            market_low=market_estimate.low_amount if market_estimate else None,
            market_high=market_estimate.high_amount if market_estimate else None,
            classification_status=(
                kb_diag.classification.value
                if hasattr(kb_diag.classification, "value")
                else str(kb_diag.classification)
            ),
            brand=listing.brand,
            model=listing.model,
            fuel_type=fuel_str,
            known_issues_count=kb_diag.issues_count,
            has_recall_campaign=kb_diag.has_recalls,
            max_severity=(
                kb_diag.max_severity.value
                if hasattr(kb_diag.max_severity, "value") and kb_diag.max_severity
                else (str(kb_diag.max_severity) if kb_diag.max_severity else None)
            ),
            repair_cost_max=kb_diag.total_estimated_repair_max,
            mitigations_count=mitigations_count,
            mileage_km=listing.mileage_km,
            year=listing.year,
            snapshots_count=len(listing.snapshots),
            price_reductions=reductions_count,
            price_increases=0,
            title=f"{listing.brand} {listing.model}",
            description=listing.description,
            days_on_market=days_on_market,
            seller_pressure_level=pressure_level,
        )

        # 8. Persistir OpportunityScore inmutable
        score = OpportunityScore(
            vehicle_id=vehicle_id,
            listing_id=listing.id,
            profile_version_id=version.id,
            total_score=eval_result["total_score"],
            price_score=eval_result["price_score"],
            reliability_score=eval_result["reliability_score"],
            liquidity_score=eval_result["liquidity_score"],
            mechanical_risk_score=eval_result["mechanical_risk_score"],
            mileage_score=eval_result["mileage_score"],
            age_score=eval_result["age_score"],
            history_score=eval_result["history_score"],
            condition_score=eval_result["condition_score"],
            listing_age_score=eval_result["listing_age_score"],
            score_breakdown=eval_result["score_breakdown"],
            calculated_at=datetime.now(UTC),
        )
        session.add(score)
        await session.flush()

        # 9. Crear o actualizar Opportunity
        op_stmt = (
            select(Opportunity)
            .options(selectinload(Opportunity.score))
            .where(Opportunity.listing_id == listing.id)
        )
        opportunity = (await session.execute(op_stmt)).scalar_one_or_none()

        if not opportunity:
            opportunity = Opportunity(
                id=uuid4(),
                vehicle_id=vehicle_id,
                listing_id=listing.id,
                score_id=score.id,
                status=OpportunityStatus.IDENTIFIED,
                currency="EUR",
                asking_price=valuation["asking_price"],
                estimated_market_price=valuation["estimated_market_price"],
                estimated_fast_sale_price=valuation["estimated_fast_sale_price"],
                target_purchase_price=valuation["target_purchase_price"],
                estimated_transfer_cost=valuation["estimated_transfer_cost"],
                estimated_tax=valuation["estimated_tax"],
                estimated_repair_min=valuation["estimated_repair_min"],
                estimated_repair_max=valuation["estimated_repair_max"],
                estimated_preparation_cost=valuation["estimated_preparation_cost"],
                estimated_total_cost_min=valuation["estimated_total_cost_min"],
                estimated_total_cost_max=valuation["estimated_total_cost_max"],
                estimated_margin_min=valuation["estimated_margin_min"],
                estimated_margin_max=valuation["estimated_margin_max"],
                estimated_roi_min=valuation["estimated_roi_min"],
                estimated_roi_max=valuation["estimated_roi_max"],
                confidence_level=valuation["confidence_level"],
                seller_pressure_level=pressure_level,
                seller_pressure_reasons=pressure_reasons,
                notes=None,
            )
            session.add(opportunity)
        else:
            opportunity.vehicle_id = vehicle_id
            opportunity.score_id = score.id
            opportunity.asking_price = valuation["asking_price"]
            opportunity.estimated_market_price = valuation["estimated_market_price"]
            opportunity.estimated_fast_sale_price = valuation["estimated_fast_sale_price"]
            opportunity.target_purchase_price = valuation["target_purchase_price"]
            opportunity.estimated_transfer_cost = valuation["estimated_transfer_cost"]
            opportunity.estimated_tax = valuation["estimated_tax"]
            opportunity.estimated_repair_min = valuation["estimated_repair_min"]
            opportunity.estimated_repair_max = valuation["estimated_repair_max"]
            opportunity.estimated_preparation_cost = valuation["estimated_preparation_cost"]
            opportunity.estimated_total_cost_min = valuation["estimated_total_cost_min"]
            opportunity.estimated_total_cost_max = valuation["estimated_total_cost_max"]
            opportunity.estimated_margin_min = valuation["estimated_margin_min"]
            opportunity.estimated_margin_max = valuation["estimated_margin_max"]
            opportunity.estimated_roi_min = valuation["estimated_roi_min"]
            opportunity.estimated_roi_max = valuation["estimated_roi_max"]
            opportunity.confidence_level = valuation["confidence_level"]
            opportunity.seller_pressure_level = pressure_level
            opportunity.seller_pressure_reasons = pressure_reasons

        await session.flush()
        await session.refresh(opportunity, ["score", "vehicle", "listing"])
        return opportunity

    @staticmethod
    async def evaluate_vehicle(
        session: AsyncSession,
        vehicle_id: UUID,
        profile_version_id: UUID | None = None,
    ) -> Opportunity:
        """Evalúa un vehículo unificado tomando su anuncio más representativo."""
        stmt = (
            select(Vehicle)
            .options(
                selectinload(Vehicle.listings).selectinload(VehicleListing.snapshots),
            )
            .where(Vehicle.id == vehicle_id)
        )
        vehicle = (await session.execute(stmt)).scalar_one_or_none()
        if not vehicle:
            raise TargetNotFoundError("vehículo", vehicle_id)

        if not vehicle.listings:
            raise TargetNotFoundError("anuncios de vehículo", vehicle_id)

        # Seleccionar el anuncio con fecha más reciente o activo
        rep_listing = sorted(
            vehicle.listings, key=lambda item: item.published_at or item.created_at, reverse=True
        )[0]
        return await ScoringService.evaluate_listing(
            session=session,
            listing_id=rep_listing.id,
            profile_version_id=profile_version_id,
        )

    # --- Listado y Consulta ---

    @staticmethod
    async def list_opportunities(
        session: AsyncSession,
        status: OpportunityStatus | None = None,
        min_score: Decimal | None = None,
        brand: str | None = None,
        seller_pressure: SellerPressureLevel | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Opportunity], int]:
        base_stmt = select(Opportunity).options(
            selectinload(Opportunity.score),
            selectinload(Opportunity.listing),
            selectinload(Opportunity.vehicle),
        )

        if status:
            base_stmt = base_stmt.where(Opportunity.status == status)
        if seller_pressure:
            base_stmt = base_stmt.where(Opportunity.seller_pressure_level == seller_pressure)
        if min_score is not None:
            base_stmt = base_stmt.join(Opportunity.score).where(
                OpportunityScore.total_score >= min_score
            )
        if brand:
            # Filtrar por marca a través de listing o vehicle
            clean_brand = brand.strip().lower()
            base_stmt = (
                base_stmt.outerjoin(Opportunity.listing)
                .outerjoin(Opportunity.vehicle)
                .where(
                    or_(
                        func.lower(VehicleListing.brand) == clean_brand,
                        func.lower(Vehicle.brand) == clean_brand,
                    )
                )
            )

        total_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = (await session.execute(total_stmt)).scalar_one()

        stmt = (
            base_stmt.order_by(Opportunity.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = (await session.execute(stmt)).scalars().all()
        return items, total

    @staticmethod
    async def get_opportunity(session: AsyncSession, opportunity_id: UUID) -> Opportunity:
        stmt = (
            select(Opportunity)
            .options(
                selectinload(Opportunity.score),
                selectinload(Opportunity.listing),
                selectinload(Opportunity.vehicle),
            )
            .where(Opportunity.id == opportunity_id)
        )
        opportunity = (await session.execute(stmt)).scalar_one_or_none()
        if not opportunity:
            raise OpportunityNotFoundError(opportunity_id)
        return opportunity

    @staticmethod
    async def update_opportunity_status(
        session: AsyncSession,
        opportunity_id: UUID,
        status: OpportunityStatus,
        notes: str | None = None,
    ) -> Opportunity:
        opportunity = await ScoringService.get_opportunity(session, opportunity_id)
        opportunity.status = status
        if notes is not None:
            opportunity.notes = notes
        await session.flush()
        return opportunity

    @staticmethod
    def map_to_read(op: Opportunity) -> OpportunityRead:
        """Convierte una entidad Opportunity a OpportunityRead completando campos de tarjeta."""
        listing = op.listing
        vehicle = op.vehicle

        brand = (listing.brand if listing else None) or (vehicle.brand if vehicle else None)
        model = (listing.model if listing else None) or (vehicle.model if vehicle else None)
        year = (listing.year if listing else None) or (vehicle.year if vehicle else None)
        fuel = None
        if listing and listing.fuel_type:
            fuel = (
                listing.fuel_type.value
                if hasattr(listing.fuel_type, "value")
                else str(listing.fuel_type)
            )
        elif vehicle and vehicle.fuel_type:
            fuel = (
                vehicle.fuel_type.value
                if hasattr(vehicle.fuel_type, "value")
                else str(vehicle.fuel_type)
            )

        trans = None
        if listing and listing.transmission:
            trans = (
                listing.transmission.value
                if hasattr(listing.transmission, "value")
                else str(listing.transmission)
            )
        elif vehicle and vehicle.transmission:
            trans = (
                vehicle.transmission.value
                if hasattr(vehicle.transmission, "value")
                else str(vehicle.transmission)
            )

        return OpportunityRead(
            id=op.id,
            vehicle_id=op.vehicle_id,
            listing_id=op.listing_id,
            score_id=op.score_id,
            status=op.status,
            currency=op.currency or "EUR",
            asking_price=op.asking_price,
            estimated_market_price=op.estimated_market_price,
            estimated_fast_sale_price=op.estimated_fast_sale_price,
            target_purchase_price=op.target_purchase_price,
            estimated_transfer_cost=op.estimated_transfer_cost,
            estimated_tax=op.estimated_tax,
            estimated_repair_min=op.estimated_repair_min,
            estimated_repair_max=op.estimated_repair_max,
            estimated_preparation_cost=op.estimated_preparation_cost,
            estimated_total_cost_min=op.estimated_total_cost_min,
            estimated_total_cost_max=op.estimated_total_cost_max,
            estimated_margin_min=op.estimated_margin_min,
            estimated_margin_max=op.estimated_margin_max,
            estimated_roi_min=op.estimated_roi_min,
            estimated_roi_max=op.estimated_roi_max,
            confidence_level=op.confidence_level,
            seller_pressure_level=op.seller_pressure_level,
            seller_pressure_reasons=op.seller_pressure_reasons or [],
            notes=op.notes,
            created_at=op.created_at,
            updated_at=op.updated_at,
            score=op.score,
            title=f"{brand} {model}" if brand and model else None,
            brand=brand,
            model=model,
            generation=vehicle.generation if vehicle else (listing.generation if listing else None),
            trim=vehicle.trim if vehicle else (listing.trim if listing else None),
            engine_code=vehicle.engine_code
            if vehicle
            else (listing.engine_code if listing else None),
            fuel_type=fuel,
            transmission=trans,
            year=year,
            mileage_km=listing.mileage_km if listing else None,
            city=listing.location if listing else None,
            province=listing.province if listing else None,
            external_url=listing.url if listing else None,
            source_name=None,
        )
