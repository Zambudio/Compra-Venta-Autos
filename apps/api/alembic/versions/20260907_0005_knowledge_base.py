"""Create Phase 4 schema: technical hierarchy, knowledge sources, evidences, issues, and classifications.

Revision ID: 20260907_0005
Revises: 20260906_0004
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260907_0005"
down_revision: str | None = "20260906_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

source_trust_level = sa.Enum(
    "A", "B", "C", "D", name="source_trust_level", native_enum=False, create_constraint=True
)
knowledge_source_type = sa.Enum(
    "OFFICIAL_RECALL",
    "STATISTICAL_REPORT",
    "TECHNICAL_MEDIA",
    "WORKSHOP_NOTE",
    "COMMUNITY_REPORT",
    name="knowledge_source_type",
    native_enum=False,
    create_constraint=True,
)
issue_severity = sa.Enum(
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
    name="issue_severity",
    native_enum=False,
    create_constraint=True,
)
issue_frequency = sa.Enum(
    "RARE",
    "OCCASIONAL",
    "FREQUENT",
    "SYSTEMIC",
    name="issue_frequency",
    native_enum=False,
    create_constraint=True,
)
issue_status = sa.Enum(
    "DRAFT",
    "REVIEWED",
    "VERIFIED",
    "DEPRECATED",
    name="issue_status",
    native_enum=False,
    create_constraint=True,
)
vehicle_component = sa.Enum(
    "ENGINE_INTERNAL",
    "TIMING_SYSTEM",
    "TURBOCHARGER",
    "FUEL_SYSTEM",
    "EMISSIONS_EGR_DPF",
    "COOLING_SYSTEM",
    "TRANSMISSION_MANUAL",
    "TRANSMISSION_AUTOMATIC",
    "CLUTCH_FLYWHEEL",
    "ELECTRICAL",
    "SUSPENSION_STEERING",
    "BRAKES",
    "BODYWORK",
    "OTHER",
    name="vehicle_component",
    native_enum=False,
    create_constraint=True,
)
classification_status = sa.Enum(
    "WHITELIST",
    "WATCHLIST",
    "BLACKLIST",
    "UNKNOWN",
    name="classification_status",
    native_enum=False,
    create_constraint=True,
)
classification_target_type = sa.Enum(
    "MODEL",
    "GENERATION",
    "ENGINE",
    "ENGINE_VARIANT",
    "TRANSMISSION",
    "COMBINATION",
    name="classification_target_type",
    native_enum=False,
    create_constraint=True,
)
transmission_type = sa.Enum(
    "MANUAL",
    "AUTOMATIC_TORQUE_CONVERTER",
    "DUAL_CLUTCH",
    "CVT",
    "AUTOMATED_MANUAL",
    "UNKNOWN",
    name="transmission_type",
    native_enum=False,
    create_constraint=True,
)
engine_aspiration = sa.Enum(
    "NATURALLY_ASPIRATED",
    "TURBOCHARGED",
    "SUPERCHARGED",
    "TWINCHARGED",
    "OTHER",
    name="engine_aspiration",
    native_enum=False,
    create_constraint=True,
)
fuel_type = sa.Enum(
    "PETROL",
    "DIESEL",
    "LPG",
    "CNG",
    "HYBRID",
    "PLUGIN_HYBRID",
    "ELECTRIC",
    "OTHER",
    name="fuel_type",
    native_enum=False,
    create_constraint=True,
)


def upgrade() -> None:
    # 1. manufacturers
    op.create_table(
        "manufacturers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("country", sa.String(length=60), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_manufacturers_name"),
    )
    op.create_index("ix_manufacturers_name", "manufacturers", ["name"])

    # 2. vehicle_models
    op.create_table(
        "vehicle_models",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("manufacturer_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["manufacturer_id"], ["manufacturers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("manufacturer_id", "name", name="uq_vehicle_models_manufacturer_name"),
    )
    op.create_index("ix_vehicle_models_manufacturer_id", "vehicle_models", ["manufacturer_id"])
    op.create_index("ix_vehicle_models_name", "vehicle_models", ["name"])

    # 3. vehicle_generations
    op.create_table(
        "vehicle_generations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("model_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("year_start", sa.Integer(), nullable=False),
        sa.Column("year_end", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "year_end IS NULL OR year_end >= year_start", name="ck_generation_years"
        ),
        sa.ForeignKeyConstraint(["model_id"], ["vehicle_models.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vehicle_generations_model_id", "vehicle_generations", ["model_id"])

    # 4. engines
    op.create_table(
        "engines",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("manufacturer_id", sa.Uuid(), nullable=False),
        sa.Column("family_code", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("displacement_cc", sa.Integer(), nullable=True),
        sa.Column("fuel_type", fuel_type, nullable=False),
        sa.Column("aspiration", engine_aspiration, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["manufacturer_id"], ["manufacturers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "manufacturer_id", "family_code", name="uq_engines_manufacturer_family"
        ),
    )
    op.create_index("ix_engines_manufacturer_id", "engines", ["manufacturer_id"])
    op.create_index("ix_engines_family_code", "engines", ["family_code"])

    # 5. engine_variants
    op.create_table(
        "engine_variants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("engine_id", sa.Uuid(), nullable=False),
        sa.Column("version_code", sa.String(length=60), nullable=True),
        sa.Column("power_kw", sa.Integer(), nullable=True),
        sa.Column("power_cv", sa.Integer(), nullable=True),
        sa.Column("torque_nm", sa.Integer(), nullable=True),
        sa.Column("year_start", sa.Integer(), nullable=True),
        sa.Column("year_end", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["engine_id"], ["engines.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_engine_variants_engine_id", "engine_variants", ["engine_id"])
    op.create_index("ix_engine_variants_version_code", "engine_variants", ["version_code"])

    # 6. transmission_specs
    op.create_table(
        "transmission_specs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("manufacturer_id", sa.Uuid(), nullable=True),
        sa.Column("code", sa.String(length=60), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("type", transmission_type, nullable=False),
        sa.Column("gears", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["manufacturer_id"], ["manufacturers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_transmission_specs_code", "transmission_specs", ["code"])

    # 7. knowledge_sources
    op.create_table(
        "knowledge_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_type", knowledge_source_type, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("publisher", sa.String(length=150), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trust_level", source_trust_level, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_sources_trust_level", "knowledge_sources", ["trust_level"])

    # 8. evidences
    op.create_table(
        "evidences",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("component", vehicle_component, nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("severity", issue_severity, nullable=False),
        sa.Column("confidence_score", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("verified_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "confidence_score >= 0.000 AND confidence_score <= 1.000", name="ck_evidence_confidence"
        ),
        sa.ForeignKeyConstraint(["source_id"], ["knowledge_sources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["verified_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evidences_source_id", "evidences", ["source_id"])
    op.create_index("ix_evidences_component", "evidences", ["component"])

    # 9. known_issues
    op.create_table(
        "known_issues",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("component", vehicle_component, nullable=False),
        sa.Column("severity", issue_severity, nullable=False),
        sa.Column("frequency", issue_frequency, nullable=False),
        sa.Column("typical_mileage_km", sa.Integer(), nullable=True),
        sa.Column("estimated_repair_cost_min", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("estimated_repair_cost_max", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="EUR", nullable=False),
        sa.Column("symptoms", sa.Text(), nullable=True),
        sa.Column("prevention", sa.Text(), nullable=True),
        sa.Column("definitive_repair", sa.Text(), nullable=True),
        sa.Column(
            "has_recall_campaign", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("recall_details", sa.Text(), nullable=True),
        sa.Column("status", issue_status, server_default="DRAFT", nullable=False),
        sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("estimated_repair_cost_min >= 0", name="ck_issue_cost_min"),
        sa.CheckConstraint(
            "estimated_repair_cost_max >= estimated_repair_cost_min", name="ck_issue_cost_range"
        ),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_known_issues_title", "known_issues", ["title"])
    op.create_index("ix_known_issues_component", "known_issues", ["component"])
    op.create_index("ix_known_issues_severity", "known_issues", ["severity"])
    op.create_index("ix_known_issues_status", "known_issues", ["status"])

    # 10. many-to-many bridge tables
    op.create_table(
        "known_issue_evidences",
        sa.Column("known_issue_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["known_issue_id"], ["known_issues.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidences.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("known_issue_id", "evidence_id"),
    )

    op.create_table(
        "known_issue_engines",
        sa.Column("known_issue_id", sa.Uuid(), nullable=False),
        sa.Column("engine_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["known_issue_id"], ["known_issues.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["engine_id"], ["engines.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("known_issue_id", "engine_id"),
    )

    op.create_table(
        "known_issue_engine_variants",
        sa.Column("known_issue_id", sa.Uuid(), nullable=False),
        sa.Column("engine_variant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["known_issue_id"], ["known_issues.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["engine_variant_id"], ["engine_variants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("known_issue_id", "engine_variant_id"),
    )

    op.create_table(
        "known_issue_generations",
        sa.Column("known_issue_id", sa.Uuid(), nullable=False),
        sa.Column("generation_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["known_issue_id"], ["known_issues.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["generation_id"], ["vehicle_generations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("known_issue_id", "generation_id"),
    )

    op.create_table(
        "known_issue_transmissions",
        sa.Column("known_issue_id", sa.Uuid(), nullable=False),
        sa.Column("transmission_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["known_issue_id"], ["known_issues.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["transmission_id"], ["transmission_specs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("known_issue_id", "transmission_id"),
    )

    # 11. vehicle_classifications
    op.create_table(
        "vehicle_classifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("target_type", classification_target_type, nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("status", classification_status, nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("validity_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("validity_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_classifications_target", "vehicle_classifications", ["target_type", "target_id"]
    )
    op.create_index("ix_classifications_status", "vehicle_classifications", ["status"])

    # 12. vehicle_mitigations
    op.create_table(
        "vehicle_mitigations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(), nullable=False),
        sa.Column("known_issue_id", sa.Uuid(), nullable=False),
        sa.Column("mitigation_type", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by_user_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["known_issue_id"], ["known_issues.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["verified_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vehicle_mitigations_vehicle_id", "vehicle_mitigations", ["vehicle_id"])
    op.create_index(
        "ix_vehicle_mitigations_known_issue_id", "vehicle_mitigations", ["known_issue_id"]
    )


def downgrade() -> None:
    op.drop_table("vehicle_mitigations")
    op.drop_table("vehicle_classifications")
    op.drop_table("known_issue_transmissions")
    op.drop_table("known_issue_generations")
    op.drop_table("known_issue_engine_variants")
    op.drop_table("known_issue_engines")
    op.drop_table("known_issue_evidences")
    op.drop_table("known_issues")
    op.drop_table("evidences")
    op.drop_table("knowledge_sources")
    op.drop_table("transmission_specs")
    op.drop_table("engine_variants")
    op.drop_table("engines")
    op.drop_table("vehicle_generations")
    op.drop_table("vehicle_models")
    op.drop_table("manufacturers")
