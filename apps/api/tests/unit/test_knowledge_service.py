"""Pruebas unitarias para KnowledgeService con AsyncMock sin dependencias externas."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
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
    Evidence,
    KnownIssue,
    Manufacturer,
    VehicleClassification,
    VehicleGeneration,
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
    TransmissionSpecCreate,
    VehicleClassificationCreate,
    VehicleGenerationCreate,
    VehicleMitigationCreate,
    VehicleModelCreate,
)
from app.knowledge.service import KnowledgeService
from app.knowledge.vocab import (
    ClassificationStatus,
    ClassificationTargetType,
    EngineAspiration,
    IssueFrequency,
    IssueSeverity,
    IssueStatus,
    KnowledgeSourceType,
    SourceTrustLevel,
    TransmissionType,
    VehicleComponent,
)
from app.listings.vocab import FuelType

pytestmark = pytest.mark.unit


def _scalar_result(value: object) -> MagicMock:
    mock = MagicMock()
    mock.scalar_one_or_none.return_value = value
    mock.scalar_one.return_value = value
    if isinstance(value, list):
        mock.scalars.return_value.all.return_value = value
    elif value is not None:
        mock.scalars.return_value.all.return_value = [value]
    else:
        mock.scalars.return_value.all.return_value = []
    return mock


@pytest.mark.asyncio
async def test_manufacturer_crud() -> None:
    session = AsyncMock()
    session.add = MagicMock()

    # 1. Crear fabricante exitoso
    m = await KnowledgeService.create_manufacturer(
        session, ManufacturerCreate(name="Peugeot", country="Francia")
    )
    assert m.id is not None
    assert m.name == "Peugeot"
    assert m.country == "Francia"
    session.add.assert_called_once()
    session.flush.assert_awaited_once()

    # 2. Obtener fabricante existente
    session.get.return_value = m
    m_get = await KnowledgeService.get_manufacturer(session, m.id)
    assert m_get.name == "Peugeot"

    # 3. Obtener fabricante inexistente lanza error
    session.get.return_value = None
    with pytest.raises(ManufacturerNotFoundError):
        await KnowledgeService.get_manufacturer(session, uuid4())

    # 4. Listar fabricantes
    session.execute.return_value = _scalar_result([m])
    items = await KnowledgeService.list_manufacturers(session)
    assert len(items) == 1
    assert items[0].name == "Peugeot"


@pytest.mark.asyncio
async def test_model_and_generation_crud() -> None:
    session = AsyncMock()
    session.add = MagicMock()

    m_id = uuid4()
    m = Manufacturer(id=m_id, name="Peugeot")

    # 1. Modelo con fabricante no existente lanza error
    session.get.return_value = None
    with pytest.raises(ManufacturerNotFoundError):
        await KnowledgeService.create_model(
            session, VehicleModelCreate(manufacturer_id=m_id, name="208")
        )

    # 2. Modelo exitoso
    session.get.return_value = m
    mod = await KnowledgeService.create_model(
        session, VehicleModelCreate(manufacturer_id=m_id, name="208")
    )
    assert mod.id is not None
    assert mod.name == "208"

    # 3. Listar modelos
    session.execute.return_value = _scalar_result([mod])
    models = await KnowledgeService.list_models(session, manufacturer_id=m_id)
    assert len(models) == 1

    # 4. Generación con modelo inexistente lanza error
    session.get.return_value = None
    with pytest.raises(VehicleModelNotFoundError):
        await KnowledgeService.create_generation(
            session, VehicleGenerationCreate(model_id=mod.id, name="208 I", year_start=2012)
        )

    # 5. Generación exitosa
    session.get.return_value = mod
    gen = await KnowledgeService.create_generation(
        session,
        VehicleGenerationCreate(model_id=mod.id, name="208 I", year_start=2012, year_end=2019),
    )
    assert gen.id is not None
    assert gen.name == "208 I"
    assert gen.year_start == 2012

    # 6. Listar generaciones
    session.execute.return_value = _scalar_result([gen])
    gens = await KnowledgeService.list_generations(session, model_id=mod.id)
    assert len(gens) == 1


@pytest.mark.asyncio
async def test_engine_and_variant_crud() -> None:
    session = AsyncMock()
    session.add = MagicMock()

    m_id = uuid4()
    m = Manufacturer(id=m_id, name="Peugeot")

    # 1. Motor con fabricante no existente
    session.get.return_value = None
    with pytest.raises(ManufacturerNotFoundError):
        await KnowledgeService.create_engine(
            session,
            EngineCreate(
                manufacturer_id=m_id,
                family_code="EB2",
                name="1.2 PureTech",
                fuel_type=FuelType.PETROL,
            ),
        )

    # 2. Motor exitoso
    session.get.return_value = m
    eng = await KnowledgeService.create_engine(
        session,
        EngineCreate(
            manufacturer_id=m_id,
            family_code="EB2",
            name="1.2 PureTech",
            displacement_cc=1199,
            fuel_type=FuelType.PETROL,
            aspiration=EngineAspiration.TURBOCHARGED,
        ),
    )
    assert eng.id is not None
    assert eng.family_code == "EB2"

    # 3. Listar motores
    session.execute.return_value = _scalar_result([eng])
    engines = await KnowledgeService.list_engines(session, manufacturer_id=m_id)
    assert len(engines) == 1

    # 4. Variante con motor inexistente
    session.get.return_value = None
    with pytest.raises(EngineNotFoundError):
        await KnowledgeService.create_engine_variant(
            session, EngineVariantCreate(engine_id=eng.id, version_code="EB2DT", power_cv=110)
        )

    # 5. Variante exitosa
    session.get.return_value = eng
    var = await KnowledgeService.create_engine_variant(
        session,
        EngineVariantCreate(
            engine_id=eng.id, version_code="EB2DT", power_cv=110, torque_nm=205, power_kw=81
        ),
    )
    assert var.id is not None
    assert var.power_cv == 110

    # 6. Listar variantes
    session.execute.return_value = _scalar_result([var])
    variants = await KnowledgeService.list_engine_variants(session, engine_id=eng.id)
    assert len(variants) == 1


@pytest.mark.asyncio
async def test_transmissions_crud() -> None:
    session = AsyncMock()
    session.add = MagicMock()

    m_id = uuid4()

    # 1. Fabricante no existente
    session.get.return_value = None
    with pytest.raises(ManufacturerNotFoundError):
        await KnowledgeService.create_transmission(
            session,
            TransmissionSpecCreate(manufacturer_id=m_id, name="BVM5", type=TransmissionType.MANUAL),
        )

    # 2. Creación exitosa
    session.get.return_value = Manufacturer(id=m_id, name="Peugeot")
    trans = await KnowledgeService.create_transmission(
        session,
        TransmissionSpecCreate(
            manufacturer_id=m_id,
            name="BVM5",
            code="MA5",
            type=TransmissionType.MANUAL,
            gears=5,
        ),
    )
    assert trans.id is not None
    assert trans.name == "BVM5"
    assert trans.gears == 5

    # 3. Listar transmisiones
    session.execute.return_value = _scalar_result([trans])
    trans_list = await KnowledgeService.list_transmissions(session)
    assert len(trans_list) == 1


@pytest.mark.asyncio
async def test_sources_and_evidences() -> None:
    session = AsyncMock()
    session.add = MagicMock()

    # 1. Crear fuente
    src_data = KnowledgeSourceCreate(
        source_type=KnowledgeSourceType.OFFICIAL_RECALL,
        name="Safety Gate Alerta A12/01504/20",
        url="https://ec.europa.eu/safety-gate",
        publisher="Comisión Europea",
        trust_level=SourceTrustLevel.A,
    )
    src = await KnowledgeService.create_source(session, src_data)
    assert src.id is not None
    assert src.trust_level == SourceTrustLevel.A
    assert src.name == "Safety Gate Alerta A12/01504/20"

    # 2. Listar fuentes
    count_mock = MagicMock()
    count_mock.scalar_one.return_value = 1
    items_mock = MagicMock()
    items_mock.scalars.return_value.all.return_value = [src]
    session.execute.side_effect = [count_mock, items_mock]

    items, total = await KnowledgeService.list_sources(session)
    assert total == 1
    assert len(items) == 1

    # 3. Crear evidencia con fuente no existente lanza error
    session.get.return_value = None
    with pytest.raises(KnowledgeSourceNotFoundError):
        await KnowledgeService.create_evidence(
            session,
            EvidenceCreate(
                source_id=src.id,
                component=VehicleComponent.TIMING_SYSTEM,
                summary="Fallo de correa",
                severity=IssueSeverity.CRITICAL,
                confidence_score=Decimal("0.950"),
            ),
        )

    # 4. Crear evidencia exitosa
    session.get.return_value = src
    ev = await KnowledgeService.create_evidence(
        session,
        EvidenceCreate(
            source_id=src.id,
            component=VehicleComponent.TIMING_SYSTEM,
            summary="Degradación de correa húmeda que provoca pérdida de asistencia de frenado.",
            severity=IssueSeverity.CRITICAL,
            confidence_score=Decimal("0.950"),
            verified=True,
        ),
        user_id=uuid4(),
    )
    assert ev.id is not None
    assert ev.severity == IssueSeverity.CRITICAL
    assert ev.verified is True
    assert ev.verified_by_user_id is not None

    # 5. Listar evidencias
    session.execute.side_effect = [count_mock, items_mock]
    _ev_items, ev_total = await KnowledgeService.list_evidences(session, verified_only=True)
    assert ev_total == 1


@pytest.mark.asyncio
async def test_known_issue_creation_and_evidence_rule() -> None:
    session = AsyncMock()
    session.add = MagicMock()

    # Plan Maestro §15: no permitir estado VERIFIED sin evidencias
    with pytest.raises(IssueCannotBeVerifiedWithoutEvidenceError):
        await KnowledgeService.create_known_issue(
            session,
            KnownIssueCreate(
                title="Avería inventada",
                description="Sin evidencias",
                component=VehicleComponent.TIMING_SYSTEM,
                severity=IssueSeverity.CRITICAL,
                frequency=IssueFrequency.SYSTEMIC,
                estimated_repair_cost_min=Decimal("500.00"),
                estimated_repair_cost_max=Decimal("1500.00"),
                status=IssueStatus.VERIFIED,
                evidence_ids=[],
            ),
        )

    # Crear issue en DRAFT sin evidencias está permitido
    draft_issue = await KnowledgeService.create_known_issue(
        session,
        KnownIssueCreate(
            title="Avería en revisión",
            description="Esperando fuentes",
            component=VehicleComponent.TIMING_SYSTEM,
            severity=IssueSeverity.HIGH,
            frequency=IssueFrequency.FREQUENT,
            estimated_repair_cost_min=Decimal("500.00"),
            estimated_repair_cost_max=Decimal("1500.00"),
            status=IssueStatus.DRAFT,
            evidence_ids=[],
        ),
    )
    assert draft_issue.status == IssueStatus.DRAFT

    # Crear issue VERIFIED con evidencias
    ev_id = uuid4()
    ev = Evidence(id=ev_id, severity=IssueSeverity.CRITICAL)
    session.execute.return_value = _scalar_result([ev])

    verified_issue = await KnowledgeService.create_known_issue(
        session,
        KnownIssueCreate(
            title="Correa húmeda",
            description="Degradación de correa en aceite",
            component=VehicleComponent.TIMING_SYSTEM,
            severity=IssueSeverity.CRITICAL,
            frequency=IssueFrequency.SYSTEMIC,
            estimated_repair_cost_min=Decimal("800.00"),
            estimated_repair_cost_max=Decimal("3500.00"),
            status=IssueStatus.VERIFIED,
            evidence_ids=[ev_id],
        ),
        user_id=uuid4(),
    )
    assert verified_issue.status == IssueStatus.VERIFIED
    assert len(verified_issue.evidences) == 1


@pytest.mark.asyncio
async def test_known_issue_update_lifecycle() -> None:
    session = AsyncMock()

    i_id = uuid4()

    # 1. Issue inexistente lanza error
    session.get.return_value = None
    with pytest.raises(KnownIssueNotFoundError):
        await KnowledgeService.update_known_issue(
            session, i_id, KnownIssueUpdate(title="Nuevo título")
        )

    # 2. Intentar pasar a VERIFIED sin evidencias lanza error
    issue = KnownIssue(
        id=i_id,
        title="Problema",
        description="Desc",
        component=VehicleComponent.COOLING_SYSTEM,
        severity=IssueSeverity.MEDIUM,
        frequency=IssueFrequency.OCCASIONAL,
        estimated_repair_cost_min=Decimal("100.00"),
        estimated_repair_cost_max=Decimal("300.00"),
        currency="EUR",
        status=IssueStatus.DRAFT,
        has_recall_campaign=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    issue.evidences = []
    session.get.return_value = issue

    with pytest.raises(IssueCannotBeVerifiedWithoutEvidenceError):
        await KnowledgeService.update_known_issue(
            session, i_id, KnownIssueUpdate(status=IssueStatus.VERIFIED)
        )

    # 3. Actualizar a VERIFIED con evidencia existente
    ev = Evidence(id=uuid4(), severity=IssueSeverity.MEDIUM)
    issue.evidences = [ev]
    user_id = uuid4()
    updated = await KnowledgeService.update_known_issue(
        session,
        i_id,
        KnownIssueUpdate(status=IssueStatus.VERIFIED, symptoms="Fuga leve"),
        user_id=user_id,
    )
    assert updated.status == IssueStatus.VERIFIED
    assert updated.reviewed_by_user_id == user_id
    assert updated.symptoms == "Fuga leve"


@pytest.mark.asyncio
async def test_classifications_and_mitigations() -> None:
    session = AsyncMock()
    session.add = MagicMock()

    eng_id = uuid4()

    # 1. Clasificación válida
    cls = await KnowledgeService.create_classification(
        session,
        VehicleClassificationCreate(
            target_type=ClassificationTargetType.ENGINE,
            target_id=eng_id,
            status=ClassificationStatus.BLACKLIST,
            rationale="Correa en baño de aceite",
        ),
    )
    assert cls.id is not None
    assert cls.status == ClassificationStatus.BLACKLIST

    # 2. Listar clasificaciones
    count_mock = MagicMock()
    count_mock.scalar_one.return_value = 1
    items_mock = MagicMock()
    items_mock.scalars.return_value.all.return_value = [cls]
    session.execute.side_effect = [count_mock, items_mock]

    cls_list, total = await KnowledgeService.list_classifications(
        session, target_type=ClassificationTargetType.ENGINE
    )
    assert total == 1
    assert len(cls_list) == 1

    # 3. Mitigación con issue no existente lanza error
    session.get.return_value = None
    v_id = uuid4()
    with pytest.raises(KnownIssueNotFoundError):
        await KnowledgeService.add_vehicle_mitigation(
            session,
            VehicleMitigationCreate(
                vehicle_id=v_id,
                known_issue_id=uuid4(),
                mitigation_type="INVOICE_PROVED_REPLACEMENT",
                description="Reemplazo preventivo con factura oficial.",
            ),
        )

    # 4. Mitigación exitosa
    session.get.return_value = KnownIssue(id=uuid4(), title="Fallo correa")
    mit = await KnowledgeService.add_vehicle_mitigation(
        session,
        VehicleMitigationCreate(
            vehicle_id=v_id,
            known_issue_id=uuid4(),
            mitigation_type="INVOICE_PROVED_REPLACEMENT",
            description="Kit sustituido en concesionario",
        ),
        user_id=uuid4(),
    )
    assert mit.id is not None
    assert mit.vehicle_id == v_id

    # 5. Listar mitigaciones
    session.execute.side_effect = None
    session.execute.return_value = _scalar_result([mit])
    mits = await KnowledgeService.list_vehicle_mitigations(session, v_id)
    assert len(mits) == 1


@pytest.mark.asyncio
async def test_lookup_vehicle_reliability_algorithm() -> None:
    session = AsyncMock()

    m_id = uuid4()
    mod_id = uuid4()
    gen_id = uuid4()
    eng_id = uuid4()

    m = Manufacturer(id=m_id, name="Peugeot")
    mod = VehicleModel(id=mod_id, manufacturer_id=m_id, name="208")
    gen = VehicleGeneration(
        id=gen_id, model_id=mod_id, name="208 I", year_start=2012, year_end=2019
    )
    eng = Engine(id=eng_id, manufacturer_id=m_id, family_code="EB2", name="1.2 PureTech")

    now = datetime.now(UTC)
    issue = KnownIssue(
        id=uuid4(),
        title="Correa húmeda degradada",
        description="Correa en baño de aceite",
        component=VehicleComponent.TIMING_SYSTEM,
        severity=IssueSeverity.CRITICAL,
        frequency=IssueFrequency.SYSTEMIC,
        estimated_repair_cost_min=Decimal("1000.00"),
        estimated_repair_cost_max=Decimal("4000.00"),
        currency="EUR",
        status=IssueStatus.VERIFIED,
        has_recall_campaign=True,
        symptoms="Aviso de presión de aceite",
        prevention="Uso estricto de aceite homologado B71 2010",
        created_at=now,
        updated_at=now,
    )
    issue.evidences = []

    cls = VehicleClassification(
        id=uuid4(),
        target_type=ClassificationTargetType.ENGINE,
        target_id=eng_id,
        status=ClassificationStatus.BLACKLIST,
        rationale="Motor con correa bañada en aceite y fallo catastrófico.",
        created_at=now,
        updated_at=now,
    )

    m_mock = _scalar_result(m)
    mod_mock = _scalar_result([mod])
    gen_mock = _scalar_result([gen])
    eng_mock = _scalar_result([eng])
    eng_issue_mock = _scalar_result([issue.id])
    gen_issue_mock = _scalar_result([])
    issues_mock = _scalar_result([issue])
    cls_mock = _scalar_result([cls])

    session.execute.side_effect = [
        m_mock,
        mod_mock,
        gen_mock,
        eng_mock,
        eng_issue_mock,
        gen_issue_mock,
        issues_mock,
        cls_mock,
    ]

    lookup = await KnowledgeService.lookup_vehicle_reliability(
        session,
        brand="Peugeot",
        model="208",
        year=2016,
        fuel_type="PETROL",
        engine_code="EB2",
    )

    assert lookup.brand == "Peugeot"
    assert lookup.model == "208"
    assert lookup.classification == ClassificationStatus.BLACKLIST
    assert lookup.issues_count == 1
    assert lookup.max_severity == IssueSeverity.CRITICAL
    assert lookup.total_estimated_repair_min == Decimal("1000.00")
    assert lookup.total_estimated_repair_max == Decimal("4000.00")
    assert lookup.has_recalls is True
    assert any("B71 2010" in r for r in lookup.preventive_recommendations)
    assert any("presión de aceite" in r for r in lookup.preventive_recommendations)
