"""Create Phase 3 schema: vehicles, match candidates, and market estimates.

Revision ID: 20260906_0004
Revises: 20260906_0003
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260906_0004"
down_revision: str | None = "20260906_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

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
transmission = sa.Enum(
    "MANUAL", "AUTOMATIC", "UNKNOWN", name="transmission", native_enum=False, create_constraint=True
)
match_candidate_status = sa.Enum(
    "PENDING",
    "CONFIRMED",
    "REJECTED",
    name="match_candidate_status",
    native_enum=False,
    create_constraint=True,
)
market_estimate_method = sa.Enum(
    "COMPARABLES_MEDIAN_IQR",
    name="market_estimate_method",
    native_enum=False,
    create_constraint=True,
)


def upgrade() -> None:
    op.create_table(
        "vehicles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("brand", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("generation", sa.String(length=120), nullable=True),
        sa.Column("trim", sa.String(length=160), nullable=True),
        sa.Column("engine_code", sa.String(length=40), nullable=True),
        sa.Column("power_kw", sa.Integer(), nullable=True),
        sa.Column("fuel_type", fuel_type, nullable=False),
        sa.Column("transmission", transmission, nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column(
            "first_listed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("listing_count", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vehicles")),
    )
    op.create_index("ix_vehicles_brand_model", "vehicles", ["brand", "model"], unique=False)
    op.create_index("ix_vehicles_year", "vehicles", ["year"], unique=False)

    op.add_column("vehicle_listings", sa.Column("vehicle_id", sa.Uuid(), nullable=True))
    op.create_index(
        op.f("ix_vehicle_listings_vehicle_id"), "vehicle_listings", ["vehicle_id"], unique=False
    )
    op.create_foreign_key(
        op.f("fk_vehicle_listings_vehicle_id_vehicles"),
        "vehicle_listings",
        "vehicles",
        ["vehicle_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "vehicle_match_candidates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("listing_a_id", sa.Uuid(), nullable=False),
        sa.Column("listing_b_id", sa.Uuid(), nullable=False),
        sa.Column("confidence_score", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("match_reasons", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", match_candidate_status, server_default="PENDING", nullable=False),
        sa.Column("decided_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "listing_a_id < listing_b_id", name=op.f("ck_vehicle_match_candidates_pair_order")
        ),
        sa.ForeignKeyConstraint(
            ["decided_by_user_id"],
            ["users.id"],
            name=op.f("fk_vehicle_match_candidates_decided_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["listing_a_id"],
            ["vehicle_listings.id"],
            name=op.f("fk_vehicle_match_candidates_listing_a_id_vehicle_listings"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["listing_b_id"],
            ["vehicle_listings.id"],
            name=op.f("fk_vehicle_match_candidates_listing_b_id_vehicle_listings"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vehicle_match_candidates")),
        sa.UniqueConstraint(
            "listing_a_id", "listing_b_id", name="uq_vehicle_match_candidates_listing_a_id"
        ),
    )
    op.create_index(
        op.f("ix_vehicle_match_candidates_listing_a_id"),
        "vehicle_match_candidates",
        ["listing_a_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_vehicle_match_candidates_listing_b_id"),
        "vehicle_match_candidates",
        ["listing_b_id"],
        unique=False,
    )
    op.create_index(
        "ix_match_candidates_status", "vehicle_match_candidates", ["status"], unique=False
    )

    op.create_table(
        "market_estimates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(), nullable=True),
        sa.Column("listing_id", sa.Uuid(), nullable=True),
        sa.Column("estimated_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("low_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("high_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="EUR", nullable=False),
        sa.Column(
            "method",
            market_estimate_method,
            server_default="COMPARABLES_MEDIAN_IQR",
            nullable=False,
        ),
        sa.Column("number_of_comparables", sa.Integer(), nullable=False),
        sa.Column("confidence_score", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column(
            "calculated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(vehicle_id IS NOT NULL) OR (listing_id IS NOT NULL)",
            name=op.f("ck_market_estimates_target_present"),
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["vehicle_listings.id"],
            name=op.f("fk_market_estimates_listing_id_vehicle_listings"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["vehicle_id"],
            ["vehicles.id"],
            name=op.f("fk_market_estimates_vehicle_id_vehicles"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_market_estimates")),
    )
    op.create_index(
        op.f("ix_market_estimates_calculated_at"),
        "market_estimates",
        ["calculated_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_market_estimates_listing_id"), "market_estimates", ["listing_id"], unique=False
    )
    op.create_index(
        op.f("ix_market_estimates_vehicle_id"), "market_estimates", ["vehicle_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_market_estimates_vehicle_id"), table_name="market_estimates")
    op.drop_index(op.f("ix_market_estimates_listing_id"), table_name="market_estimates")
    op.drop_index(op.f("ix_market_estimates_calculated_at"), table_name="market_estimates")
    op.drop_table("market_estimates")

    op.drop_index("ix_match_candidates_status", table_name="vehicle_match_candidates")
    op.drop_index(
        op.f("ix_vehicle_match_candidates_listing_b_id"), table_name="vehicle_match_candidates"
    )
    op.drop_index(
        op.f("ix_vehicle_match_candidates_listing_a_id"), table_name="vehicle_match_candidates"
    )
    op.drop_table("vehicle_match_candidates")

    op.drop_constraint(
        op.f("fk_vehicle_listings_vehicle_id_vehicles"), "vehicle_listings", type_="foreignkey"
    )
    op.drop_index(op.f("ix_vehicle_listings_vehicle_id"), table_name="vehicle_listings")
    op.drop_column("vehicle_listings", "vehicle_id")

    op.drop_index("ix_vehicles_year", table_name="vehicles")
    op.drop_index("ix_vehicles_brand_model", table_name="vehicles")
    op.drop_table("vehicles")
