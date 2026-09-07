"""Pruebas unitarias para endpoints de Knowledge Base."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from app.auth.dependencies import AuthContext, get_db, require_auth, require_csrf
from app.auth.models import AuthSession
from app.core.config import Environment, Settings
from app.knowledge.models import (
    KnowledgeSource,
    KnownIssue,
    Manufacturer,
)
from app.knowledge.vocab import (
    ClassificationStatus,
    IssueFrequency,
    IssueSeverity,
    IssueStatus,
    KnowledgeSourceType,
    SourceTrustLevel,
    VehicleComponent,
)
from app.main import create_app
from app.users.models import User, UserRole
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.unit


def _settings() -> Settings:
    return Settings(
        environment=Environment.TEST,
        database_url="postgresql+psycopg://u:p@db:5432/t",
        redis_url=SecretStr("redis://:p@redis:6379/0"),
        cors_origins=["http://testserver"],
        allowed_hosts=["testserver"],
        session_cookie_secure=False,
    )


def _ctx(role: UserRole = UserRole.OWNER) -> AuthContext:
    user = User(id=uuid4(), email="u@example.com", password_hash="h", role=role, is_active=True)
    session = AuthSession(
        id=uuid4(),
        user_id=user.id,
        token_hash="t",
        csrf_token_hash="c",
        expires_at=datetime(2999, 1, 1, tzinfo=UTC),
    )
    return AuthContext(user=user, session=session)


async def _dummy_db() -> AsyncIterator[AsyncSession]:
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.commit = AsyncMock()
    yield mock_session


@pytest.fixture
def app():
    with patch("app.main.Database"), patch("app.main.RedisClient"):
        application = create_app(_settings())
        application.dependency_overrides[get_db] = _dummy_db
        application.dependency_overrides[require_auth] = lambda: _ctx(UserRole.OWNER)
        application.dependency_overrides[require_csrf] = lambda: _ctx(UserRole.OWNER)
        yield application


@pytest.mark.asyncio
async def test_manufacturers_and_models_endpoints(app) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Crear fabricante
        m_id = uuid4()
        fake_m = Manufacturer(id=m_id, name="Peugeot", country="Francia")
        fake_m.created_at = datetime.now(UTC)
        fake_m.updated_at = datetime.now(UTC)

        with patch(
            "app.knowledge.service.KnowledgeService.create_manufacturer", return_value=fake_m
        ):
            res = await client.post(
                "/api/v1/knowledge/manufacturers", json={"name": "Peugeot", "country": "Francia"}
            )
            assert res.status_code == 201
            assert res.json()["name"] == "Peugeot"

        # 2. Listar fabricantes
        with patch(
            "app.knowledge.service.KnowledgeService.list_manufacturers", return_value=[fake_m]
        ):
            res = await client.get("/api/v1/knowledge/manufacturers")
            assert res.status_code == 200
            assert len(res.json()) == 1


@pytest.mark.asyncio
async def test_sources_and_evidences_endpoints(app) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        src_id = uuid4()
        fake_src = KnowledgeSource(
            id=src_id,
            source_type=KnowledgeSourceType.OFFICIAL_RECALL,
            name="Safety Gate",
            trust_level=SourceTrustLevel.A,
            retrieved_at=datetime.now(UTC),
        )
        fake_src.created_at = datetime.now(UTC)
        fake_src.updated_at = datetime.now(UTC)

        # Crear fuente
        with patch("app.knowledge.service.KnowledgeService.create_source", return_value=fake_src):
            res = await client.post(
                "/api/v1/knowledge/sources",
                json={
                    "source_type": "OFFICIAL_RECALL",
                    "name": "Safety Gate",
                    "trust_level": "A",
                },
            )
            assert res.status_code == 201
            assert res.json()["trust_level"] == "A"

        # Listar fuentes
        with patch(
            "app.knowledge.service.KnowledgeService.list_sources", return_value=([fake_src], 1)
        ):
            res = await client.get("/api/v1/knowledge/sources")
            assert res.status_code == 200
            assert res.json()["total"] == 1


@pytest.mark.asyncio
async def test_known_issues_endpoints(app) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        i_id = uuid4()
        fake_issue = KnownIssue(
            id=i_id,
            title="Correa húmeda defectuosa",
            description="Degradación en aceite",
            component=VehicleComponent.TIMING_SYSTEM,
            severity=IssueSeverity.CRITICAL,
            frequency=IssueFrequency.SYSTEMIC,
            estimated_repair_cost_min=Decimal("800.00"),
            estimated_repair_cost_max=Decimal("4000.00"),
            currency="EUR",
            status=IssueStatus.VERIFIED,
            has_recall_campaign=False,
        )
        fake_issue.created_at = datetime.now(UTC)
        fake_issue.updated_at = datetime.now(UTC)

        # Crear issue
        with patch(
            "app.knowledge.service.KnowledgeService.create_known_issue", return_value=fake_issue
        ):
            res = await client.post(
                "/api/v1/knowledge/issues",
                json={
                    "title": "Correa húmeda defectuosa",
                    "description": "Degradación en aceite",
                    "component": "TIMING_SYSTEM",
                    "severity": "CRITICAL",
                    "frequency": "SYSTEMIC",
                    "estimated_repair_cost_min": "800.00",
                    "estimated_repair_cost_max": "4000.00",
                    "status": "VERIFIED",
                    "evidence_ids": [str(uuid4())],
                },
            )
            assert res.status_code == 201
            assert res.json()["severity"] == "CRITICAL"

        # Listar issues
        with patch(
            "app.knowledge.service.KnowledgeService.list_known_issues",
            return_value=([fake_issue], 1),
        ):
            res = await client.get("/api/v1/knowledge/issues")
            assert res.status_code == 200
            assert res.json()["total"] == 1


@pytest.mark.asyncio
async def test_reliability_lookup_endpoint(app) -> None:
    from app.knowledge.schemas import ReliabilityLookupResponse

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        fake_resp = ReliabilityLookupResponse(
            brand="Peugeot",
            model="208",
            year=2016,
            fuel_type="PETROL",
            engine_code="EB2",
            classification=ClassificationStatus.BLACKLIST,
            classification_rationale="Motor con riesgo crítico documentado.",
            issues_count=1,
            max_severity=IssueSeverity.CRITICAL,
            total_estimated_repair_min=Decimal("1000.00"),
            total_estimated_repair_max=Decimal("4000.00"),
            currency="EUR",
            has_recalls=True,
            issues=[],
            preventive_recommendations=["Medir grosor de correa"],
        )

        with patch(
            "app.knowledge.service.KnowledgeService.lookup_vehicle_reliability",
            return_value=fake_resp,
        ):
            res = await client.get(
                "/api/v1/knowledge/reliability-lookup",
                params={"brand": "Peugeot", "model": "208", "year": 2016, "fuel_type": "PETROL"},
            )
            assert res.status_code == 200
            data = res.json()
            assert data["classification"] == "BLACKLIST"
            assert data["issues_count"] == 1
            assert data["max_severity"] == "CRITICAL"
            assert data["has_recalls"] is True
