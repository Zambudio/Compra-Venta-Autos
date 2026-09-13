"""Add persisted source configuration and its audit trail.

Revision ID: 20260913_0010
Revises: 20260912_0009
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260913_0010"
down_revision: str | None = "20260912_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "source_configurations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source_key", sa.String(length=32), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "config",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("last_sync", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["source_key"], ["sources.key"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_key"),
    )
    op.create_table(
        "source_config_changes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source_key", sa.String(length=32), nullable=False),
        sa.Column("before", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("after", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("changed_by", sa.UUID(), nullable=True),
        sa.Column(
            "changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["changed_by"], ["users.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["source_key"], ["sources.key"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_source_config_changes_changed_by",
        "source_config_changes",
        ["changed_by"],
    )
    op.create_index(
        "ix_source_config_changes_source_changed",
        "source_config_changes",
        ["source_key", "changed_at"],
    )

    op.execute(
        """
        INSERT INTO source_configurations
            (id, source_key, enabled, config, created_at, updated_at)
        SELECT gen_random_uuid(), key, is_active, '{}'::jsonb, now(), now()
        FROM sources
        WHERE key IN ('manual', 'wallapop')
        ON CONFLICT (source_key) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_source_config_changes_source_changed", table_name="source_config_changes"
    )
    op.drop_index(
        "ix_source_config_changes_changed_by", table_name="source_config_changes"
    )
    op.drop_table("source_config_changes")
    op.drop_table("source_configurations")
