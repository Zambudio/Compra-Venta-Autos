"""Create Phase 2 acquisition schema: sources and vehicle listings.

Revision ID: 20260906_0002
Revises: 20260906_0001
Create Date: 2026-09-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260906_0002"
down_revision: str | None = "20260906_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

provider_kind = sa.Enum(
    "MOCK", "MANUAL", "CONNECTOR", name="provider_kind", native_enum=False, create_constraint=True
)
sync_run_status = sa.Enum(
    "PENDING",
    "RUNNING",
    "SUCCESS",
    "PARTIAL",
    "FAILED",
    name="sync_run_status",
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
transmission = sa.Enum(
    "MANUAL", "AUTOMATIC", "UNKNOWN", name="transmission", native_enum=False, create_constraint=True
)
seller_type = sa.Enum(
    "PRIVATE", "DEALER", "UNKNOWN", name="seller_type", native_enum=False, create_constraint=True
)
listing_status = sa.Enum(
    "ACTIVE",
    "WITHDRAWN",
    "UNKNOWN",
    name="listing_status",
    native_enum=False,
    create_constraint=True,
)
entry_channel = sa.Enum(
    "MOCK_SYNC", "MANUAL_ENTRY", name="entry_channel", native_enum=False, create_constraint=True
)


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("provider_kind", provider_kind, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_automatable", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sources")),
        sa.UniqueConstraint("key", name=op.f("uq_sources_key")),
    )

    op.create_table(
        "source_compliance_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("acquisition_method", sa.String(length=120), nullable=False),
        sa.Column("automated_allowed", sa.Boolean(), nullable=False),
        sa.Column("authentication_required", sa.String(length=120), nullable=False),
        sa.Column("rate_limit", sa.String(length=120), nullable=True),
        sa.Column("terms_url", sa.String(length=2048), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
            name=op.f("fk_source_compliance_reviews_source_id_sources"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_compliance_reviews")),
    )
    op.create_index(
        op.f("ix_source_compliance_reviews_source_id"),
        "source_compliance_reviews",
        ["source_id"],
        unique=False,
    )
    op.create_index(
        "ix_source_compliance_reviews_source_checked",
        "source_compliance_reviews",
        ["source_id", "checked_at"],
        unique=False,
    )

    op.create_table(
        "source_sync_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("status", sync_run_status, nullable=False),
        sa.Column("mode", sa.String(length=10), nullable=False),
        sa.Column(
            "filters",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("job_id", sa.String(length=64), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("listings_seen", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("listings_created", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("listings_updated", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("snapshots_created", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_summary", sa.String(length=500), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
            name=op.f("fk_source_sync_runs_source_id_sources"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_sync_runs")),
    )
    op.create_index(
        op.f("ix_source_sync_runs_source_id"), "source_sync_runs", ["source_id"], unique=False
    )
    op.create_index(
        "ix_source_sync_runs_source_created",
        "source_sync_runs",
        ["source_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "vehicle_listings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("brand", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("generation", sa.String(length=120), nullable=True),
        sa.Column("trim", sa.String(length=160), nullable=True),
        sa.Column("engine_code", sa.String(length=40), nullable=True),
        sa.Column("power_kw", sa.Integer(), nullable=True),
        sa.Column("fuel_type", fuel_type, nullable=False),
        sa.Column("transmission", transmission, nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("mileage_km", sa.Integer(), nullable=False),
        sa.Column("price_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "price_currency", sa.String(length=3), nullable=False, server_default=sa.text("'EUR'")
        ),
        sa.Column("location", sa.String(length=160), nullable=True),
        sa.Column("province", sa.String(length=80), nullable=True),
        sa.Column("seller_type", seller_type, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "image_urls",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("status", listing_status, nullable=False, server_default=sa.text("'ACTIVE'")),
        sa.Column("entry_channel", entry_channel, nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
            name=op.f("fk_vehicle_listings_source_id_sources"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vehicle_listings")),
        sa.UniqueConstraint(
            "source_id", "external_id", name="uq_vehicle_listings_source_id_external_id"
        ),
    )
    op.create_index(
        op.f("ix_vehicle_listings_source_id"), "vehicle_listings", ["source_id"], unique=False
    )
    op.create_index(
        "ix_vehicle_listings_brand_model", "vehicle_listings", ["brand", "model"], unique=False
    )
    op.create_index(
        "ix_vehicle_listings_price_amount", "vehicle_listings", ["price_amount"], unique=False
    )
    op.create_index("ix_vehicle_listings_year", "vehicle_listings", ["year"], unique=False)
    op.create_index(
        "ix_vehicle_listings_last_seen_at", "vehicle_listings", ["last_seen_at"], unique=False
    )
    op.create_index("ix_vehicle_listings_status", "vehicle_listings", ["status"], unique=False)

    op.create_table(
        "raw_listing_payloads",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("listing_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("connector_version", sa.String(length=20), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["vehicle_listings.id"],
            name=op.f("fk_raw_listing_payloads_listing_id_vehicle_listings"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
            name=op.f("fk_raw_listing_payloads_source_id_sources"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_raw_listing_payloads")),
        sa.UniqueConstraint(
            "source_id", "payload_hash", name="uq_raw_listing_payloads_source_id_payload_hash"
        ),
    )
    op.create_index(
        op.f("ix_raw_listing_payloads_listing_id"),
        "raw_listing_payloads",
        ["listing_id"],
        unique=False,
    )
    op.create_index(
        "ix_raw_listing_payloads_listing_id_retrieved_at",
        "raw_listing_payloads",
        ["listing_id", "retrieved_at"],
        unique=False,
    )

    op.create_table(
        "listing_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("listing_id", sa.Uuid(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("price_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "price_currency", sa.String(length=3), nullable=False, server_default=sa.text("'EUR'")
        ),
        sa.Column("mileage_km", sa.Integer(), nullable=False),
        sa.Column("status", listing_status, nullable=False),
        sa.Column("description_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["vehicle_listings.id"],
            name=op.f("fk_listing_snapshots_listing_id_vehicle_listings"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_listing_snapshots")),
    )
    op.create_index(
        op.f("ix_listing_snapshots_listing_id"), "listing_snapshots", ["listing_id"], unique=False
    )
    op.create_index(
        "ix_listing_snapshots_listing_id_observed_at",
        "listing_snapshots",
        ["listing_id", "observed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_listing_snapshots_listing_id_observed_at", table_name="listing_snapshots")
    op.drop_index(op.f("ix_listing_snapshots_listing_id"), table_name="listing_snapshots")
    op.drop_table("listing_snapshots")

    op.drop_index(
        "ix_raw_listing_payloads_listing_id_retrieved_at", table_name="raw_listing_payloads"
    )
    op.drop_index(op.f("ix_raw_listing_payloads_listing_id"), table_name="raw_listing_payloads")
    op.drop_table("raw_listing_payloads")

    op.drop_index("ix_vehicle_listings_status", table_name="vehicle_listings")
    op.drop_index("ix_vehicle_listings_last_seen_at", table_name="vehicle_listings")
    op.drop_index("ix_vehicle_listings_year", table_name="vehicle_listings")
    op.drop_index("ix_vehicle_listings_price_amount", table_name="vehicle_listings")
    op.drop_index("ix_vehicle_listings_brand_model", table_name="vehicle_listings")
    op.drop_index(op.f("ix_vehicle_listings_source_id"), table_name="vehicle_listings")
    op.drop_table("vehicle_listings")

    op.drop_index("ix_source_sync_runs_source_created", table_name="source_sync_runs")
    op.drop_index(op.f("ix_source_sync_runs_source_id"), table_name="source_sync_runs")
    op.drop_table("source_sync_runs")

    op.drop_index(
        "ix_source_compliance_reviews_source_checked", table_name="source_compliance_reviews"
    )
    op.drop_index(
        op.f("ix_source_compliance_reviews_source_id"), table_name="source_compliance_reviews"
    )
    op.drop_table("source_compliance_reviews")

    op.drop_table("sources")
