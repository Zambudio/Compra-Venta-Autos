from __future__ import annotations

import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

_PHASE2_TABLES = {
    "sources",
    "source_compliance_reviews",
    "source_sync_runs",
    "vehicle_listings",
    "raw_listing_payloads",
    "listing_snapshots",
}


async def _table_names() -> set[str]:
    engine = create_async_engine(os.environ["TEST_DATABASE_URL"])
    try:
        async with engine.connect() as connection:
            return set(
                await connection.run_sync(
                    lambda sync_connection: inspect(sync_connection).get_table_names()
                )
            )
    finally:
        await engine.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_phase2_migration_round_trips() -> None:
    config = Config("alembic.ini")

    command.downgrade(config, "20260906_0001")
    assert _PHASE2_TABLES.isdisjoint(await _table_names())

    command.upgrade(config, "head")
    tables = await _table_names()
    assert _PHASE2_TABLES <= tables

    # base -> head still lands on the same schema
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    assert _PHASE2_TABLES <= await _table_names()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_seed_creates_mock_and_manual_sources_idempotently() -> None:
    config = Config("alembic.ini")
    command.upgrade(config, "head")

    engine = create_async_engine(os.environ["TEST_DATABASE_URL"])
    try:
        async with engine.connect() as connection:
            keys = (
                (await connection.execute(text("SELECT key FROM sources ORDER BY key")))
                .scalars()
                .all()
            )
            reviews = (
                await connection.execute(text("SELECT count(*) FROM source_compliance_reviews"))
            ).scalar_one()
        assert keys == ["manual", "mock"]
        assert reviews == 2

        # Re-running the data migration must not duplicate rows.
        command.downgrade(config, "20260906_0002")
        command.upgrade(config, "head")
        async with engine.connect() as connection:
            keys_again = (
                (await connection.execute(text("SELECT key FROM sources ORDER BY key")))
                .scalars()
                .all()
            )
            reviews_again = (
                await connection.execute(text("SELECT count(*) FROM source_compliance_reviews"))
            ).scalar_one()
        assert keys_again == ["manual", "mock"]
        assert reviews_again == 2
    finally:
        await engine.dispose()
