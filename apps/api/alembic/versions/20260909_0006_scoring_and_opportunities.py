"""Create Phase 5 schema: scoring profiles, versions, opportunity scores, and opportunities.

Revision ID: 20260909_0006
Revises: 20260907_0005
Create Date: 2026-09-09
"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20260909_0006"
down_revision: str | None = "20260907_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

opportunity_status = sa.Enum(
    "IDENTIFIED",
    "ANALYZING",
    "VALIDATED",
    "DISCARDED",
    name="opportunity_status",
    native_enum=False,
    create_constraint=True,
)
confidence_level = sa.Enum(
    "LOW",
    "MEDIUM",
    "HIGH",
    name="confidence_level",
    native_enum=False,
    create_constraint=True,
)
seller_pressure_level = sa.Enum(
    "LOW",
    "MEDIUM",
    "HIGH",
    name="seller_pressure_level",
    native_enum=False,
    create_constraint=True,
)

DEFAULT_PROFILE_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")
DEFAULT_VERSION_ID = uuid.UUID("11111111-1111-4111-8111-111111111112")


def upgrade() -> None:
    # 1. scoring_profiles
    op.create_table(
        "scoring_profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
        sa.UniqueConstraint("name", name="uq_scoring_profiles_name"),
        sa.UniqueConstraint("slug", name="uq_scoring_profiles_slug"),
    )
    op.create_index("ix_scoring_profiles_slug", "scoring_profiles", ["slug"])

    # 2. scoring_profile_versions
    op.create_table(
        "scoring_profile_versions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("profile_id", sa.UUID(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("weights", JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "config", JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'"), nullable=False
        ),
        sa.Column("is_immutable", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
        sa.ForeignKeyConstraint(["profile_id"], ["scoring_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "version_number", name="uq_profile_version"),
    )
    op.create_index(
        "ix_scoring_profile_versions_profile_id",
        "scoring_profile_versions",
        ["profile_id"],
    )

    # 3. opportunity_scores
    op.create_table(
        "opportunity_scores",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("vehicle_id", sa.UUID(), nullable=True),
        sa.Column("listing_id", sa.UUID(), nullable=True),
        sa.Column("profile_version_id", sa.UUID(), nullable=False),
        sa.Column("total_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("price_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("reliability_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("liquidity_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("mechanical_risk_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("mileage_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("age_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("history_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("condition_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("listing_age_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("score_breakdown", JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "calculated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(vehicle_id IS NOT NULL) OR (listing_id IS NOT NULL)",
            name="score_target_present",
        ),
        sa.ForeignKeyConstraint(["listing_id"], ["vehicle_listings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["profile_version_id"], ["scoring_profile_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_opportunity_scores_calc_at", "opportunity_scores", ["calculated_at"])
    op.create_index("ix_opportunity_scores_listing_id", "opportunity_scores", ["listing_id"])
    op.create_index(
        "ix_opportunity_scores_profile_version_id", "opportunity_scores", ["profile_version_id"]
    )
    op.create_index("ix_opportunity_scores_total", "opportunity_scores", ["total_score"])
    op.create_index("ix_opportunity_scores_vehicle_id", "opportunity_scores", ["vehicle_id"])

    # 4. opportunities
    op.create_table(
        "opportunities",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("vehicle_id", sa.UUID(), nullable=True),
        sa.Column("listing_id", sa.UUID(), nullable=True),
        sa.Column("score_id", sa.UUID(), nullable=True),
        sa.Column("status", opportunity_status, nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="EUR", nullable=False),
        sa.Column("asking_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("estimated_market_price", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("estimated_fast_sale_price", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("target_purchase_price", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "estimated_transfer_cost",
            sa.Numeric(precision=12, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column(
            "estimated_tax",
            sa.Numeric(precision=12, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column(
            "estimated_repair_min",
            sa.Numeric(precision=12, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column(
            "estimated_repair_max",
            sa.Numeric(precision=12, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column(
            "estimated_preparation_cost",
            sa.Numeric(precision=12, scale=2),
            server_default="200.00",
            nullable=False,
        ),
        sa.Column("estimated_total_cost_min", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("estimated_total_cost_max", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("estimated_margin_min", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("estimated_margin_max", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("estimated_roi_min", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("estimated_roi_max", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("confidence_level", confidence_level, nullable=False),
        sa.Column("seller_pressure_level", seller_pressure_level, nullable=False),
        sa.Column(
            "seller_pressure_reasons",
            JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
        sa.Column("notes", sa.String(length=2000), nullable=True),
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
            "(vehicle_id IS NOT NULL) OR (listing_id IS NOT NULL)",
            name="opportunity_target_present",
        ),
        sa.ForeignKeyConstraint(["listing_id"], ["vehicle_listings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["score_id"], ["opportunity_scores.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_opportunities_created", "opportunities", ["created_at"])
    op.create_index("ix_opportunities_listing_id", "opportunities", ["listing_id"])
    op.create_index("ix_opportunities_score_id", "opportunities", ["score_id"])
    op.create_index("ix_opportunities_status", "opportunities", ["status"])
    op.create_index("ix_opportunities_vehicle_id", "opportunities", ["vehicle_id"])

    # 5. Seed default ScoringProfile and Version 1 (Plan Maestro §18)
    scoring_profiles_table = sa.table(
        "scoring_profiles",
        sa.column("id", sa.UUID()),
        sa.column("name", sa.String()),
        sa.column("slug", sa.String()),
        sa.column("description", sa.String()),
        sa.column("is_active", sa.Boolean()),
    )
    scoring_versions_table = sa.table(
        "scoring_profile_versions",
        sa.column("id", sa.UUID()),
        sa.column("profile_id", sa.UUID()),
        sa.column("version_number", sa.Integer()),
        sa.column("weights", JSONB(astext_type=sa.Text())),
        sa.column("config", JSONB(astext_type=sa.Text())),
        sa.column("is_immutable", sa.Boolean()),
    )

    op.bulk_insert(
        scoring_profiles_table,
        [
            {
                "id": DEFAULT_PROFILE_ID,
                "name": "Oportunidad Reventa Rápida",
                "slug": "reventa-rapida",
                "description": "Perfil estándar para vehículos populares de hasta 3.000 € con reventa ágil y mecánica contrastada (Plan Maestro §18).",
                "is_active": True,
            }
        ],
    )
    default_weights = {
        "price_score": 0.25,
        "reliability_score": 0.20,
        "liquidity_score": 0.15,
        "mechanical_risk_score": 0.15,
        "mileage_score": 0.08,
        "age_score": 0.05,
        "history_score": 0.05,
        "condition_score": 0.05,
        "listing_age_score": 0.02,
    }
    default_config = {
        "fast_sale_discount_ratio": 0.88,
        "preparation_cost_default": 200.0,
        "transfer_tax_ratio": 0.04,
        "transfer_fee_dgt": 55.70,
        "target_roi_min": 25.0,
    }
    op.bulk_insert(
        scoring_versions_table,
        [
            {
                "id": DEFAULT_VERSION_ID,
                "profile_id": DEFAULT_PROFILE_ID,
                "version_number": 1,
                "weights": default_weights,
                "config": default_config,
                "is_immutable": True,
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("opportunities")
    op.drop_table("opportunity_scores")
    op.drop_table("scoring_profile_versions")
    op.drop_table("scoring_profiles")
