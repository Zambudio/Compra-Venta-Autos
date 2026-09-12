"""Servicio de dominio para Knowledge Base, evidencias mecánicas y clasificaciones."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.knowledge.errors import (
    EngineNotFoundError,
    IssueCannotBeVerifiedWithoutEvidenceError,
    KnowledgeSourceNotFoundError,
    KnownIssueNotFoundError,
    ManufacturerNotFoundError,
    VehicleModelNotFoundError,
)
from app.knowledge.models import (
    Engine,
    EngineVariant,
    Evidence,
    KnowledgeSource,
    KnownIssue,
    Manufacturer,
    TransmissionSpec,
    VehicleClassification,
    VehicleGeneration,
    VehicleMitigation,
    VehicleModel,
)
from app.knowledge.schemas import (
    EngineCreate,
    EngineVariantCreate,
    EvidenceCreate,
    KnowledgeSourceCreate,
    KnownIssueCreate,
    KnownIssueUpdate,
    ManufacturerCreate,
    ReliabilityLookupResponse,
    TransmissionSpecCreate,
    VehicleClassificationCreate,
    VehicleGenerationCreate,
    VehicleMitigationCreate,
    VehicleModelCreate,
)
from app.knowledge.vocab import (
    ClassificationStatus,
    ClassificationTargetType,
    IssueSeverity,
    IssueStatus,
    VehicleComponent,
)
from app.listings.vocab import FuelType


class KnowledgeService:
    """Coordinador de casos de uso del dominio Knowledge Base."""

    # --- Jerarquía Técnica ---

    @staticmethod
    async def create_manufacturer(session: AsyncSession, data: ManufacturerCreate) -> Manufacturer:
        m = Manufacturer(id=uuid4(), name=data.name.strip(), country=data.country)
        session.add(m)
        await session.flush()
        return m

    @staticmethod
    async def list_manufacturers(
        session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[Manufacturer]:
        stmt = select(Manufacturer).order_by(Manufacturer.name).offset(skip).limit(limit)
        res = await session.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def get_manufacturer(session: AsyncSession, manufacturer_id: UUID) -> Manufacturer:
        m = await session.get(Manufacturer, manufacturer_id)
        if not m:
            raise ManufacturerNotFoundError(manufacturer_id)
        return m

    @staticmethod
    async def create_model(session: AsyncSession, data: VehicleModelCreate) -> VehicleModel:
        await KnowledgeService.get_manufacturer(session, data.manufacturer_id)
        model = VehicleModel(
            id=uuid4(), manufacturer_id=data.manufacturer_id, name=data.name.strip()
        )
        session.add(model)
        await session.flush()
        return model

    @staticmethod
    async def list_models(
        session: AsyncSession, manufacturer_id: UUID | None = None
    ) -> Sequence[VehicleModel]:
        stmt = select(VehicleModel).order_by(VehicleModel.name)
        if manufacturer_id:
            stmt = stmt.where(VehicleModel.manufacturer_id == manufacturer_id)
        res = await session.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def create_generation(
        session: AsyncSession, data: VehicleGenerationCreate
    ) -> VehicleGeneration:
        model = await session.get(VehicleModel, data.model_id)
        if not model:
            raise VehicleModelNotFoundError(data.model_id)
        gen = VehicleGeneration(
            id=uuid4(),
            model_id=data.model_id,
            name=data.name.strip(),
            year_start=data.year_start,
            year_end=data.year_end,
        )
        session.add(gen)
        await session.flush()
        return gen

    @staticmethod
    async def list_generations(
        session: AsyncSession, model_id: UUID | None = None
    ) -> Sequence[VehicleGeneration]:
        stmt = select(VehicleGeneration).order_by(VehicleGeneration.year_start)
        if model_id:
            stmt = stmt.where(VehicleGeneration.model_id == model_id)
        res = await session.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def create_engine(session: AsyncSession, data: EngineCreate) -> Engine:
        await KnowledgeService.get_manufacturer(session, data.manufacturer_id)
        engine = Engine(
            id=uuid4(),
            manufacturer_id=data.manufacturer_id,
            family_code=data.family_code.strip().upper(),
            name=data.name.strip(),
            displacement_cc=data.displacement_cc,
            fuel_type=data.fuel_type,
            aspiration=data.aspiration,
        )
        session.add(engine)
        await session.flush()
        return engine

    @staticmethod
    async def list_engines(
        session: AsyncSession,
        manufacturer_id: UUID | None = None,
        fuel_type: FuelType | None = None,
    ) -> Sequence[Engine]:
        stmt = select(Engine).order_by(Engine.family_code)
        if manufacturer_id:
            stmt = stmt.where(Engine.manufacturer_id == manufacturer_id)
        if fuel_type:
            stmt = stmt.where(Engine.fuel_type == fuel_type)
        res = await session.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def create_engine_variant(
        session: AsyncSession, data: EngineVariantCreate
    ) -> EngineVariant:
        engine = await session.get(Engine, data.engine_id)
        if not engine:
            raise EngineNotFoundError(data.engine_id)
        variant = EngineVariant(
            id=uuid4(),
            engine_id=data.engine_id,
            version_code=data.version_code.strip().upper() if data.version_code else None,
            power_kw=data.power_kw,
            power_cv=data.power_cv,
            torque_nm=data.torque_nm,
            year_start=data.year_start,
            year_end=data.year_end,
        )
        session.add(variant)
        await session.flush()
        return variant

    @staticmethod
    async def list_engine_variants(
        session: AsyncSession, engine_id: UUID | None = None
    ) -> Sequence[EngineVariant]:
        stmt = select(EngineVariant).order_by(EngineVariant.power_cv)
        if engine_id:
            stmt = stmt.where(EngineVariant.engine_id == engine_id)
        res = await session.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def create_transmission(
        session: AsyncSession, data: TransmissionSpecCreate
    ) -> TransmissionSpec:
        if data.manufacturer_id is not None:
            await KnowledgeService.get_manufacturer(session, data.manufacturer_id)
        trans = TransmissionSpec(
            id=uuid4(),
            manufacturer_id=data.manufacturer_id,
            code=data.code.strip().upper() if data.code else None,
            name=data.name.strip(),
            type=data.type,
            gears=data.gears,
        )
        session.add(trans)
        await session.flush()
        return trans

    @staticmethod
    async def list_transmissions(session: AsyncSession) -> Sequence[TransmissionSpec]:
        stmt = select(TransmissionSpec).order_by(TransmissionSpec.name)
        res = await session.execute(stmt)
        return res.scalars().all()

    # --- Fuentes y Evidencias ---

    @staticmethod
    async def create_source(session: AsyncSession, data: KnowledgeSourceCreate) -> KnowledgeSource:
        src = KnowledgeSource(
            id=uuid4(),
            source_type=data.source_type,
            name=data.name.strip(),
            url=data.url.strip() if data.url else None,
            publisher=data.publisher.strip() if data.publisher else None,
            published_at=data.published_at,
            retrieved_at=datetime.now(UTC),
            trust_level=data.trust_level,
            notes=data.notes,
        )
        session.add(src)
        await session.flush()
        return src

    @staticmethod
    async def list_sources(
        session: AsyncSession, page: int = 1, page_size: int = 20
    ) -> tuple[Sequence[KnowledgeSource], int]:
        total_stmt = select(func.count(KnowledgeSource.id))
        total = (await session.execute(total_stmt)).scalar_one()

        stmt = (
            select(KnowledgeSource)
            .order_by(KnowledgeSource.trust_level, KnowledgeSource.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = (await session.execute(stmt)).scalars().all()
        return items, total

    @staticmethod
    async def create_evidence(
        session: AsyncSession, data: EvidenceCreate, user_id: UUID | None = None
    ) -> Evidence:
        src = await session.get(KnowledgeSource, data.source_id)
        if not src:
            raise KnowledgeSourceNotFoundError(data.source_id)

        ev = Evidence(
            id=uuid4(),
            source_id=data.source_id,
            component=data.component,
            summary=data.summary.strip(),
            severity=data.severity,
            confidence_score=data.confidence_score,
            verified=data.verified,
            verified_by_user_id=user_id if data.verified else None,
            verified_at=datetime.now(UTC) if data.verified else None,
        )
        session.add(ev)
        await session.flush()
        ev.source = src
        return ev

    @staticmethod
    async def list_evidences(
        session: AsyncSession,
        component: VehicleComponent | None = None,
        verified_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Evidence], int]:
        base_stmt = select(Evidence)
        if component:
            base_stmt = base_stmt.where(Evidence.component == component)
        if verified_only:
            base_stmt = base_stmt.where(Evidence.verified.is_(True))

        total_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = (await session.execute(total_stmt)).scalar_one()

        stmt = (
            base_stmt.options(selectinload(Evidence.source))
            .order_by(Evidence.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = (await session.execute(stmt)).scalars().all()
        return items, total

    # --- Problemas Conocidos ---

    @staticmethod
    async def create_known_issue(
        session: AsyncSession, data: KnownIssueCreate, user_id: UUID | None = None
    ) -> KnownIssue:
        # Plan Maestro §15: no permitir estado VERIFIED sin evidencias
        if data.status == IssueStatus.VERIFIED and not data.evidence_ids:
            raise IssueCannotBeVerifiedWithoutEvidenceError("new_issue")

        issue = KnownIssue(
            id=uuid4(),
            title=data.title.strip(),
            description=data.description.strip(),
            component=data.component,
            severity=data.severity,
            frequency=data.frequency,
            typical_mileage_km=data.typical_mileage_km,
            estimated_repair_cost_min=data.estimated_repair_cost_min,
            estimated_repair_cost_max=data.estimated_repair_cost_max,
            currency=data.currency,
            symptoms=data.symptoms,
            prevention=data.prevention,
            definitive_repair=data.definitive_repair,
            has_recall_campaign=data.has_recall_campaign,
            recall_details=data.recall_details,
            status=data.status,
            reviewed_by_user_id=user_id
            if data.status in (IssueStatus.REVIEWED, IssueStatus.VERIFIED)
            else None,
            reviewed_at=datetime.now(UTC)
            if data.status in (IssueStatus.REVIEWED, IssueStatus.VERIFIED)
            else None,
        )

        # Vincular evidencias
        if data.evidence_ids:
            ev_stmt = select(Evidence).where(Evidence.id.in_(data.evidence_ids))
            evs = (await session.execute(ev_stmt)).scalars().all()
            issue.evidences.extend(evs)

        # Vincular motores
        if data.engine_ids:
            eng_stmt = select(Engine).where(Engine.id.in_(data.engine_ids))
            engs = (await session.execute(eng_stmt)).scalars().all()
            issue.engines.extend(engs)

        # Vincular variantes
        if data.engine_variant_ids:
            var_stmt = select(EngineVariant).where(EngineVariant.id.in_(data.engine_variant_ids))
            vars_ = (await session.execute(var_stmt)).scalars().all()
            issue.engine_variants.extend(vars_)

        # Vincular generaciones
        if data.generation_ids:
            gen_stmt = select(VehicleGeneration).where(
                VehicleGeneration.id.in_(data.generation_ids)
            )
            gens = (await session.execute(gen_stmt)).scalars().all()
            issue.generations.extend(gens)

        # Vincular transmisiones
        if data.transmission_ids:
            trans_stmt = select(TransmissionSpec).where(
                TransmissionSpec.id.in_(data.transmission_ids)
            )
            trans_ = (await session.execute(trans_stmt)).scalars().all()
            issue.transmissions.extend(trans_)

        session.add(issue)
        await session.flush()
        return issue

    @staticmethod
    async def update_known_issue(
        session: AsyncSession, issue_id: UUID, data: KnownIssueUpdate, user_id: UUID | None = None
    ) -> KnownIssue:
        issue = await session.get(
            KnownIssue,
            issue_id,
            options=[
                selectinload(KnownIssue.evidences),
                selectinload(KnownIssue.engines),
                selectinload(KnownIssue.engine_variants),
                selectinload(KnownIssue.generations),
                selectinload(KnownIssue.transmissions),
            ],
        )
        if not issue:
            raise KnownIssueNotFoundError(issue_id)

        # Si se actualizan evidencias
        if data.evidence_ids is not None:
            ev_stmt = select(Evidence).where(Evidence.id.in_(data.evidence_ids))
            evs = (await session.execute(ev_stmt)).scalars().all()
            issue.evidences = list(evs)

        # Plan Maestro §15: no permitir estado VERIFIED sin evidencias
        new_status = data.status or issue.status
        if new_status == IssueStatus.VERIFIED and not issue.evidences:
            raise IssueCannotBeVerifiedWithoutEvidenceError(issue_id)

        # Actualizar atributos simples
        for field, value in data.model_dump(
            exclude_unset=True,
            exclude={
                "evidence_ids",
                "engine_ids",
                "engine_variant_ids",
                "generation_ids",
                "transmission_ids",
            },
        ).items():
            setattr(issue, field, value)

        if data.status in (IssueStatus.REVIEWED, IssueStatus.VERIFIED):
            issue.reviewed_by_user_id = user_id
            issue.reviewed_at = datetime.now(UTC)

        await session.flush()
        return issue

    @staticmethod
    async def list_known_issues(
        session: AsyncSession,
        component: VehicleComponent | None = None,
        severity: IssueSeverity | None = None,
        status: IssueStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[KnownIssue], int]:
        base_stmt = select(KnownIssue)
        if component:
            base_stmt = base_stmt.where(KnownIssue.component == component)
        if severity:
            base_stmt = base_stmt.where(KnownIssue.severity == severity)
        if status:
            base_stmt = base_stmt.where(KnownIssue.status == status)

        total_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = (await session.execute(total_stmt)).scalar_one()

        stmt = (
            base_stmt.options(
                selectinload(KnownIssue.evidences).selectinload(Evidence.source),
                selectinload(KnownIssue.engines),
                selectinload(KnownIssue.engine_variants),
                selectinload(KnownIssue.generations),
                selectinload(KnownIssue.transmissions),
            )
            .order_by(KnownIssue.severity.desc(), KnownIssue.title)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = (await session.execute(stmt)).scalars().all()
        return items, total

    @staticmethod
    async def get_known_issue_detail(session: AsyncSession, issue_id: UUID) -> KnownIssue:
        stmt = (
            select(KnownIssue)
            .where(KnownIssue.id == issue_id)
            .options(
                selectinload(KnownIssue.evidences).selectinload(Evidence.source),
                selectinload(KnownIssue.engines),
                selectinload(KnownIssue.engine_variants),
                selectinload(KnownIssue.generations),
                selectinload(KnownIssue.transmissions),
            )
        )
        res = await session.execute(stmt)
        issue = res.scalar_one_or_none()
        if not issue:
            raise KnownIssueNotFoundError(issue_id)
        return issue

    # --- Clasificaciones de Fiabilidad ---

    @staticmethod
    async def create_classification(
        session: AsyncSession, data: VehicleClassificationCreate
    ) -> VehicleClassification:
        cls_obj = VehicleClassification(
            id=uuid4(),
            target_type=data.target_type,
            target_id=data.target_id,
            status=data.status,
            rationale=data.rationale.strip(),
            validity_start=data.validity_start,
            validity_end=data.validity_end,
        )
        session.add(cls_obj)
        await session.flush()
        return cls_obj

    @staticmethod
    async def list_classifications(
        session: AsyncSession,
        status: ClassificationStatus | None = None,
        target_type: ClassificationTargetType | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[VehicleClassification], int]:
        base_stmt = select(VehicleClassification)
        if status:
            base_stmt = base_stmt.where(VehicleClassification.status == status)
        if target_type:
            base_stmt = base_stmt.where(VehicleClassification.target_type == target_type)

        total_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = (await session.execute(total_stmt)).scalar_one()

        stmt = (
            base_stmt.order_by(VehicleClassification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = (await session.execute(stmt)).scalars().all()
        return items, total

    # --- Diagnóstico y Lookup de Fiabilidad ---

    @staticmethod
    async def lookup_vehicle_reliability(
        session: AsyncSession,
        brand: str,
        model: str,
        year: int | None = None,
        fuel_type: str | None = None,
        engine_code: str | None = None,
    ) -> ReliabilityLookupResponse:
        """Resuelve el diagnóstico técnico y fiabilidad para un vehículo dado."""
        clean_brand = brand.strip().lower()
        clean_model = model.strip().lower()

        # 1. Localizar Manufacturer
        m_stmt = select(Manufacturer).where(func.lower(Manufacturer.name) == clean_brand)
        m = (await session.execute(m_stmt)).scalar_one_or_none()

        matching_models: list[VehicleModel] = []
        matching_generations: list[VehicleGeneration] = []
        matching_engines: list[Engine] = []

        if m:
            # 2. Localizar Model
            mod_stmt = select(VehicleModel).where(
                VehicleModel.manufacturer_id == m.id,
                func.lower(VehicleModel.name).contains(clean_model),
            )
            matching_models = list((await session.execute(mod_stmt)).scalars().all())

            # 3. Localizar Generación si hay año
            if matching_models and year:
                model_ids = [mod.id for mod in matching_models]
                gen_stmt = select(VehicleGeneration).where(
                    VehicleGeneration.model_id.in_(model_ids),
                    VehicleGeneration.year_start <= year,
                    or_(VehicleGeneration.year_end.is_(None), VehicleGeneration.year_end >= year),
                )
                matching_generations = list((await session.execute(gen_stmt)).scalars().all())

            # 4. Localizar Motor si hay código o combustible
            eng_stmt = select(Engine).where(Engine.manufacturer_id == m.id)
            if engine_code:
                eng_stmt = eng_stmt.where(
                    func.lower(Engine.family_code).contains(engine_code.strip().lower())
                )
            if fuel_type:
                try:
                    parsed_fuel = FuelType(fuel_type)
                    eng_stmt = eng_stmt.where(Engine.fuel_type == parsed_fuel)
                except ValueError:
                    pass
            matching_engines = list((await session.execute(eng_stmt)).scalars().all())

        # 5. Obtener problemas conocidos verificados vinculados a estas entidades
        issue_ids: set[UUID] = set()

        # A través de motores
        if matching_engines:
            e_ids = [eng.id for eng in matching_engines]
            eng_issue_stmt = (
                select(KnownIssue.id)
                .join(KnownIssue.engines)
                .where(KnownIssue.status == IssueStatus.VERIFIED, Engine.id.in_(e_ids))
            )
            issue_ids.update((await session.execute(eng_issue_stmt)).scalars().all())

        # A través de generaciones
        if matching_generations:
            g_ids = [g.id for g in matching_generations]
            gen_issue_stmt = (
                select(KnownIssue.id)
                .join(KnownIssue.generations)
                .where(KnownIssue.status == IssueStatus.VERIFIED, VehicleGeneration.id.in_(g_ids))
            )
            issue_ids.update((await session.execute(gen_issue_stmt)).scalars().all())

        issues: list[KnownIssue] = []
        if issue_ids:
            issues_stmt = (
                select(KnownIssue)
                .where(KnownIssue.id.in_(issue_ids))
                .options(selectinload(KnownIssue.evidences))
                .order_by(KnownIssue.severity.desc())
            )
            issues = list((await session.execute(issues_stmt)).scalars().all())

        # 6. Determinar clasificación por especificidad
        # Prioridad: ENGINE > GENERATION > MODEL
        classification = ClassificationStatus.UNKNOWN
        rationale: str | None = None

        target_ids_to_check: list[UUID] = []
        if matching_engines:
            target_ids_to_check.extend(e.id for e in matching_engines)
        if matching_generations:
            target_ids_to_check.extend(g.id for g in matching_generations)
        if matching_models:
            target_ids_to_check.extend(mod.id for mod in matching_models)

        if target_ids_to_check:
            cls_stmt = (
                select(VehicleClassification)
                .where(VehicleClassification.target_id.in_(target_ids_to_check))
                .order_by(VehicleClassification.created_at.desc())
            )
            found_classifications = (await session.execute(cls_stmt)).scalars().all()
            if found_classifications:
                classification = found_classifications[0].status
                rationale = found_classifications[0].rationale

        # Si no hay clasificación formal explícita pero hay problemas críticos
        if classification == ClassificationStatus.UNKNOWN and issues:
            severities = [i.severity for i in issues]
            if IssueSeverity.CRITICAL in severities:
                classification = ClassificationStatus.BLACKLIST
                rationale = (
                    "Detección automática: motor con avería crítica documentada y verificada."
                )
            elif IssueSeverity.HIGH in severities:
                classification = ClassificationStatus.WATCHLIST
                rationale = (
                    "Detección automática: vehículo con averías de alta severidad conocidas."
                )

        # 7. Métricas de costes y severidad
        max_sev: IssueSeverity | None = None
        cost_min = Decimal("0.0")
        cost_max = Decimal("0.0")
        has_recalls = False
        recs: list[str] = []

        sev_rank = {
            IssueSeverity.LOW: 1,
            IssueSeverity.MEDIUM: 2,
            IssueSeverity.HIGH: 3,
            IssueSeverity.CRITICAL: 4,
        }
        highest_rank = 0

        for iss in issues:
            cost_min += iss.estimated_repair_cost_min
            cost_max += iss.estimated_repair_cost_max
            if iss.has_recall_campaign:
                has_recalls = True
            r = sev_rank.get(iss.severity, 0)
            if r > highest_rank:
                highest_rank = r
                max_sev = iss.severity
            if iss.prevention and iss.prevention not in recs:
                recs.append(iss.prevention)
            if iss.symptoms and f"Síntoma a vigilar: {iss.symptoms}" not in recs:
                recs.append(f"Síntoma a vigilar: {iss.symptoms}")

        return ReliabilityLookupResponse(
            brand=brand,
            model=model,
            year=year,
            fuel_type=fuel_type,
            engine_code=engine_code,
            classification=classification,
            classification_rationale=rationale,
            issues_count=len(issues),
            max_severity=max_sev,
            total_estimated_repair_min=cost_min,
            total_estimated_repair_max=cost_max,
            currency="EUR",
            has_recalls=has_recalls,
            issues=issues,
            preventive_recommendations=recs,
        )

    # --- Mitigaciones en Vehículos Concretos ---

    @staticmethod
    async def add_vehicle_mitigation(
        session: AsyncSession, data: VehicleMitigationCreate, user_id: UUID | None = None
    ) -> VehicleMitigation:
        issue = await session.get(KnownIssue, data.known_issue_id)
        if not issue:
            raise KnownIssueNotFoundError(data.known_issue_id)

        mit = VehicleMitigation(
            id=uuid4(),
            vehicle_id=data.vehicle_id,
            known_issue_id=data.known_issue_id,
            mitigation_type=data.mitigation_type.strip(),
            description=data.description.strip(),
            applied_at=data.applied_at or datetime.now(UTC),
            verified_by_user_id=user_id,
        )
        session.add(mit)
        await session.flush()
        mit.known_issue = issue
        return mit

    @staticmethod
    async def list_vehicle_mitigations(
        session: AsyncSession, vehicle_id: UUID
    ) -> Sequence[VehicleMitigation]:
        stmt = (
            select(VehicleMitigation)
            .where(VehicleMitigation.vehicle_id == vehicle_id)
            .options(
                selectinload(VehicleMitigation.known_issue)
                .selectinload(KnownIssue.evidences)
                .selectinload(Evidence.source),
                selectinload(VehicleMitigation.known_issue).selectinload(KnownIssue.engines),
                selectinload(VehicleMitigation.known_issue).selectinload(
                    KnownIssue.engine_variants
                ),
                selectinload(VehicleMitigation.known_issue).selectinload(KnownIssue.generations),
                selectinload(VehicleMitigation.known_issue).selectinload(KnownIssue.transmissions),
            )
            .order_by(VehicleMitigation.applied_at.desc())
        )
        res = await session.execute(stmt)
        return res.scalars().all()
