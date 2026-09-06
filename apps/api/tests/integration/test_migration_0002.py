from __future__ import annotations

import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

_PHASE2_TABLES = {
    "sources",
    "source_compliance_reviews",
    "source_sync_runs",
    "vehicle_listings",
    "raw_listing_payloads",
    "listing_snapshots",
}


def _table_names() -> set[str]:
    engine = create_engine(os.environ["TEST_DATABASE_URL"])
    try:
        with engine.connect() as connection:
            return set(inspect(connection).get_table_names())
    finally:
        engine.dispose()


@pytest.mark.integration
def test_phase2_migration_round_trips() -> None:
    config = Config("alembic.ini")

    command.downgrade(config, "20260906_0001")
    assert _PHASE2_TABLES.isdisjoint(_table_names())

    command.upgrade(config, "head")
    assert _PHASE2_TABLES <= _table_names()

    command.downgrade(config, "base")
    command.upgrade(config, "head")
    assert _PHASE2_TABLES <= _table_names()


@pytest.mark.integration
def test_seed_creates_mock_and_manual_sources_idempotently() -> None:
    config = Config("alembic.ini")
    command.upgrade(config, "head")

    engine = create_engine(os.environ["TEST_DATABASE_URL"])
    try:
        with engine.connect() as connection:
            keys = list(connection.execute(text("SELECT key FROM sources ORDER BY key")).scalars())
            reviews = connection.execute(
                text("SELECT count(*) FROM source_compliance_reviews")
            ).scalar_one()
        assert keys == ["manual", "mock"]
        assert reviews == 2

        command.downgrade(config, "20260906_0002")
        command.upgrade(config, "head")
        with engine.connect() as connection:
            keys_again = list(
                connection.execute(text("SELECT key FROM sources ORDER BY key")).scalars()
            )
            reviews_again = connection.execute(
                text("SELECT count(*) FROM source_compliance_reviews")
            ).scalar_one()
        assert keys_again == ["manual", "mock"]
        assert reviews_again == 2
    finally:
        engine.dispose()
