"""Create Phase 6 schema: watchlist, inspections, checks and file attachments.

Revision ID: 20260912_0007
Revises: 20260909_0006
Create Date: 2026-09-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260912_0007"
down_revision: str | None = "20260909_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

inspection_status = sa.Enum(
    "DRAFT",
    "IN_PROGRESS",
    "COMPLETED",
    "CANCELLED",
    name="inspection_status",
    native_enum=False,
    create_constraint=True,
)

check_result = sa.Enum(
    "PASS",
    "WARNING",
    "FAIL",
    "NOT_CHECKED",
    name="check_result",
    native_enum=False,
    create_constraint=True,
)


def upgrade() -> None:
    # 1. watchlist_entries
    op.create_table(
        "watchlist_entries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("opportunity_id", sa.UUID(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("opportunity_id", name="uq_watchlist_entries_opportunity_id"),
    )
    op.create_index(
        "ix_watchlist_entries_opportunity_id", "watchlist_entries", ["opportunity_id"]
    )

    # 2. inspections
    op.create_table(
        "inspections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("watchlist_entry_id", sa.UUID(), nullable=False),
        sa.Column("status", inspection_status, nullable=False),
        sa.Column("inspector_name", sa.String(length=100), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["watchlist_entry_id"], ["watchlist_entries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inspections_watchlist_entry_id", "inspections", ["watchlist_entry_id"])

    # 3. inspection_checks
    op.create_table(
        "inspection_checks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("inspection_id", sa.UUID(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("known_issue_id", sa.UUID(), nullable=True),
        sa.Column("result", check_result, nullable=False),
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
        sa.ForeignKeyConstraint(["inspection_id"], ["inspections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["known_issue_id"], ["known_issues.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inspection_checks_inspection_id", "inspection_checks", ["inspection_id"])

    # 4. file_attachments
    op.create_table(
        "file_attachments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("inspection_id", sa.UUID(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(length=1000), nullable=False),
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
        sa.ForeignKeyConstraint(["inspection_id"], ["inspections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_file_attachments_inspection_id", "file_attachments", ["inspection_id"])


def downgrade() -> None:
    op.drop_table("file_attachments")
    op.drop_table("inspection_checks")
    op.drop_table("inspections")
    op.drop_table("watchlist_entries")
