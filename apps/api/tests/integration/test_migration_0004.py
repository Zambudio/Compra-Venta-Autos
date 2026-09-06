from __future__ import annotations

import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

_PHASE3_TABLES = {
    "vehicles",
    "vehicle_match_candidates",
    "market_estimates",
}


def _inspect_db() -> tuple[set[str], set[str]]:
    engine = create_engine(os.environ["TEST_DATABASE_URL"])
    try:
        with engine.connect() as connection:
            inspector = inspect(connection)
            tables = set(inspector.get_table_names())
            columns: set[str] = set()
            if "vehicle_listings" in tables:
                columns = {c["name"] for c in inspector.get_columns("vehicle_listings")}
            return tables, columns
    finally:
        engine.dispose()


@pytest.mark.integration
def test_phase3_migration_round_trips() -> None:
    config = Config("alembic.ini")

    command.upgrade(config, "20260906_0003")
    tables, columns = _inspect_db()
    assert _PHASE3_TABLES.isdisjoint(tables)
    assert "vehicle_id" not in columns

    command.upgrade(config, "head")
    tables, columns = _inspect_db()
    assert _PHASE3_TABLES <= tables
    assert "vehicle_id" in columns

    command.downgrade(config, "20260906_0003")
    tables, columns = _inspect_db()
    assert _PHASE3_TABLES.isdisjoint(tables)
    assert "vehicle_id" not in columns

    command.upgrade(config, "head")
    tables, columns = _inspect_db()
    assert _PHASE3_TABLES <= tables
    assert "vehicle_id" in columns
