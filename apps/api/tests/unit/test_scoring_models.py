"""Tests unitarios para modelos y esquemas Pydantic de scoring (Fase 5)."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import app.models  # noqa: F401
import pytest
from pydantic import ValidationError

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
from app.scoring.vocab import (
    DEFAULT_SCORING_WEIGHTS,
    ConfidenceLevel,
    OpportunityStatus,
    ScoringComponent,
    SellerPressureLevel,
)


@pytest.mark.unit
def test_scoring_profile_version_validation() -> None:
    # 1. Pesos válidos que suman 1.000
    valid_dto = ScoringProfileVersionCreate(weights=dict(DEFAULT_SCORING_WEIGHTS))
    assert sum(valid_dto.weights.values()) == 1.0

    # 2. Pesos que no suman 1.000
    invalid_weights = dict(DEFAULT_SCORING_WEIGHTS)
    invalid_weights[ScoringComponent.PRICE.value] = 0.50
    with pytest.raises(ValidationError):
        ScoringProfileVersionCreate(weights=invalid_weights)

    # 3. Componente faltante
    missing_weights = dict(DEFAULT_SCORING_WEIGHTS)
    del missing_weights[ScoringComponent.PRICE.value]
    with pytest.raises(ValidationError):
        ScoringProfileVersionCreate(weights=missing_weights)

    # 4. Peso fuera de rango
    out_of_range = dict(DEFAULT_SCORING_WEIGHTS)
    out_of_range[ScoringComponent.PRICE.value] = -0.10
    out_of_range[ScoringComponent.RELIABILITY.value] = 0.45
    with pytest.raises(ValidationError):
        ScoringProfileVersionCreate(weights=out_of_range)


@pytest.mark.unit
def test_scoring_profile_create_validation() -> None:
    profile_dto = ScoringProfileCreate(
        name="Perfil Personalizado",
        slug="perfil-personalizado",
        description="Descripción de prueba",
    )
    assert profile_dto.name == "Perfil Personalizado"
    assert profile_dto.slug == "perfil-personalizado"

    # Con pesos iniciales inválidos
    bad_weights = dict(DEFAULT_SCORING_WEIGHTS)
    bad_weights[ScoringComponent.PRICE.value] = 0.10
    with pytest.raises(ValidationError):
        ScoringProfileCreate(
            name="Perfil Malo",
            slug="perfil-malo",
            initial_weights=bad_weights,
        )


@pytest.mark.unit
def test_opportunity_model_and_dto_mapping() -> None:
    op_id = uuid4()
    opportunity = Opportunity(
        id=op_id,
        status=OpportunityStatus.IDENTIFIED,
        currency="EUR",
        asking_price=Decimal("1900.00"),
        estimated_market_price=Decimal("2500.00"),
        estimated_fast_sale_price=Decimal("2200.00"),
        target_purchase_price=Decimal("1400.00"),
        estimated_transfer_cost=Decimal("131.70"),
        estimated_tax=Decimal("76.00"),
        estimated_repair_min=Decimal("50.00"),
        estimated_repair_max=Decimal("250.00"),
        estimated_preparation_cost=Decimal("200.00"),
        estimated_total_cost_min=Decimal("2281.70"),
        estimated_total_cost_max=Decimal("2481.70"),
        estimated_margin_min=Decimal("-281.70"),
        estimated_margin_max=Decimal("-81.70"),
        estimated_roi_min=Decimal("-11.35"),
        estimated_roi_max=Decimal("-3.58"),
        confidence_level=ConfidenceLevel.MEDIUM,
        seller_pressure_level=SellerPressureLevel.LOW,
        seller_pressure_reasons=["Publicado hace 3 días"],
        notes="Revisar en detalle",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    read_dto = OpportunityRead.model_validate(opportunity)
    assert read_dto.id == op_id
    assert read_dto.asking_price == Decimal("1900.00")
    assert read_dto.status == OpportunityStatus.IDENTIFIED
    assert read_dto.confidence_level == ConfidenceLevel.MEDIUM
    assert read_dto.seller_pressure_level == SellerPressureLevel.LOW
