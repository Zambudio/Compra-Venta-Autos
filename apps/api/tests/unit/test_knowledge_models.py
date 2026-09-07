"""Pruebas unitarias de modelos de Knowledge Base."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
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


def test_manufacturer_instantiation() -> None:
    m = Manufacturer(name="Peugeot", country="Francia")
    assert m.name == "Peugeot"
    assert m.country == "Francia"


def test_vehicle_model_and_generation_instantiation() -> None:
    mid = uuid4()
    model = VehicleModel(manufacturer_id=mid, name="208")
    assert model.manufacturer_id == mid
    assert model.name == "208"

    gen = VehicleGeneration(model_id=model.id, name="208 I", year_start=2012, year_end=2019)
    assert gen.name == "208 I"
    assert gen.year_start == 2012
    assert gen.year_end == 2019


def test_engine_and_variant_instantiation() -> None:
    mid = uuid4()
    eng = Engine(
        manufacturer_id=mid,
        family_code="EB2",
        name="1.2 PureTech",
        displacement_cc=1199,
        fuel_type=FuelType.PETROL,
        aspiration=EngineAspiration.TURBOCHARGED,
    )
    assert eng.family_code == "EB2"
    assert eng.displacement_cc == 1199

    var = EngineVariant(
        engine_id=eng.id,
        version_code="EB2DT",
        power_kw=81,
        power_cv=110,
        torque_nm=205,
    )
    assert var.version_code == "EB2DT"
    assert var.power_cv == 110


def test_transmission_spec_instantiation() -> None:
    trans = TransmissionSpec(
        name="BVM5",
        code="MA5",
        type=TransmissionType.MANUAL,
        gears=5,
    )
    assert trans.name == "BVM5"
    assert trans.gears == 5


def test_knowledge_source_and_evidence_instantiation() -> None:
    from datetime import UTC, datetime

    src = KnowledgeSource(
        source_type=KnowledgeSourceType.OFFICIAL_RECALL,
        name="Safety Gate UE - Campaña Correa PureTech",
        url="https://ec.europa.eu/safety-gate-alerts",
        publisher="Comisión Europea",
        published_at=datetime(2020, 11, 15, tzinfo=UTC),
        retrieved_at=datetime.now(UTC),
        trust_level=SourceTrustLevel.A,
    )
    assert src.trust_level == SourceTrustLevel.A
    assert src.source_type == KnowledgeSourceType.OFFICIAL_RECALL

    ev = Evidence(
        source_id=src.id,
        component=VehicleComponent.TIMING_SYSTEM,
        summary="Degradación prematura de la correa en baño de aceite y obstrucción de chupona.",
        severity=IssueSeverity.CRITICAL,
        confidence_score=Decimal("0.950"),
        verified=True,
    )
    assert ev.severity == IssueSeverity.CRITICAL
    assert ev.confidence_score == Decimal("0.950")
    assert ev.verified is True


def test_known_issue_instantiation() -> None:
    issue = KnownIssue(
        title="Desgaste prematuro correa distribución húmeda",
        description="La correa se deshace disolviéndose en el aceite motor obstruyendo la bomba.",
        component=VehicleComponent.TIMING_SYSTEM,
        severity=IssueSeverity.CRITICAL,
        frequency=IssueFrequency.SYSTEMIC,
        typical_mileage_km=60000,
        estimated_repair_cost_min=Decimal("800.00"),
        estimated_repair_cost_max=Decimal("4500.00"),
        currency="EUR",
        has_recall_campaign=True,
        status=IssueStatus.VERIFIED,
    )
    assert issue.title.startswith("Desgaste")
    assert issue.severity == IssueSeverity.CRITICAL
    assert issue.estimated_repair_cost_min == Decimal("800.00")
    assert issue.has_recall_campaign is True


def test_vehicle_classification_instantiation() -> None:
    target_id = uuid4()
    cls_obj = VehicleClassification(
        target_type=ClassificationTargetType.ENGINE,
        target_id=target_id,
        status=ClassificationStatus.BLACKLIST,
        rationale="Motor con correa bañada propensa a degradación y fallo de frenada.",
    )
    assert cls_obj.target_id == target_id
    assert cls_obj.status == ClassificationStatus.BLACKLIST


def test_vehicle_mitigation_instantiation() -> None:
    vid = uuid4()
    iid = uuid4()
    mit = VehicleMitigation(
        vehicle_id=vid,
        known_issue_id=iid,
        mitigation_type="INVOICE_PROVED_REPLACEMENT",
        description="Correa y chupona sustituidas en servicio oficial con factura acreditada.",
    )
    assert mit.vehicle_id == vid
    assert mit.known_issue_id == iid
    assert mit.mitigation_type == "INVOICE_PROVED_REPLACEMENT"
