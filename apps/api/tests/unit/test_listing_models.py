from __future__ import annotations

import app.models  # noqa: F401 - register every model on the shared metadata
import pytest
from app.core.models import Base
from sqlalchemy import Numeric, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB


def _table(name: str) -> Table:
    return Base.metadata.tables[name]


def _unique_column_sets(name: str) -> set[frozenset[str]]:
    return {
        frozenset(col.name for col in constraint.columns)
        for constraint in _table(name).constraints
        if isinstance(constraint, UniqueConstraint)
    }


@pytest.mark.unit
def test_all_phase2_tables_registered() -> None:
    assert {
        "sources",
        "source_compliance_reviews",
        "source_sync_runs",
        "vehicle_listings",
        "raw_listing_payloads",
        "listing_snapshots",
    } <= set(Base.metadata.tables)


@pytest.mark.unit
def test_listing_is_unique_per_source_and_external_id() -> None:
    assert frozenset({"source_id", "external_id"}) in _unique_column_sets("vehicle_listings")


@pytest.mark.unit
def test_raw_payload_is_unique_per_source_and_hash() -> None:
    assert frozenset({"source_id", "payload_hash"}) in _unique_column_sets("raw_listing_payloads")


@pytest.mark.unit
def test_source_key_is_unique() -> None:
    assert frozenset({"key"}) in _unique_column_sets("sources")


@pytest.mark.unit
@pytest.mark.parametrize("table_name", ["vehicle_listings", "listing_snapshots"])
def test_money_columns_use_numeric(table_name: str) -> None:
    assert isinstance(_table(table_name).c["price_amount"].type, Numeric)


@pytest.mark.unit
def test_raw_payload_column_is_jsonb() -> None:
    assert isinstance(_table("raw_listing_payloads").c["payload"].type, JSONB)


@pytest.mark.unit
def test_raw_payload_is_immutable_has_no_updated_at() -> None:
    assert "updated_at" not in _table("raw_listing_payloads").c


@pytest.mark.unit
def test_listing_has_expected_indexes() -> None:
    indexed = {
        frozenset(col.name for col in index.columns) for index in _table("vehicle_listings").indexes
    }
    assert frozenset({"brand", "model"}) in indexed
    assert frozenset({"last_seen_at"}) in indexed


@pytest.mark.unit
def test_snapshot_and_raw_payload_cascade_from_listing() -> None:
    for table_name in ("raw_listing_payloads", "listing_snapshots"):
        listing_fk = next(fk for fk in _table(table_name).c["listing_id"].foreign_keys)
        assert listing_fk.ondelete == "CASCADE"


@pytest.mark.unit
def test_compliance_review_and_sync_run_link_to_source() -> None:
    assert _table("source_compliance_reviews").c["source_id"].foreign_keys
    assert _table("source_sync_runs").c["source_id"].foreign_keys
