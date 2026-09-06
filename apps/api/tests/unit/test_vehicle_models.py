from __future__ import annotations

import app.models  # noqa: F401 - register all models on Base.metadata
import pytest
from app.core.models import Base
from sqlalchemy import CheckConstraint, Numeric, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB


def _table(name: str) -> Table:
    return Base.metadata.tables[name]


def _unique_column_sets(name: str) -> set[frozenset[str]]:
    return {
        frozenset(col.name for col in constraint.columns)
        for constraint in _table(name).constraints
        if isinstance(constraint, UniqueConstraint)
    }


def _check_constraints(name: str) -> list[CheckConstraint]:
    return [c for c in _table(name).constraints if isinstance(c, CheckConstraint)]


@pytest.mark.unit
def test_all_phase3_tables_registered() -> None:
    assert {
        "vehicles",
        "vehicle_match_candidates",
        "market_estimates",
    } <= set(Base.metadata.tables)


@pytest.mark.unit
def test_vehicle_listing_has_nullable_vehicle_fk() -> None:
    listings_table = _table("vehicle_listings")
    assert "vehicle_id" in listings_table.c
    col = listings_table.c["vehicle_id"]
    assert col.nullable is True
    fk = next(iter(col.foreign_keys))
    assert fk.target_fullname == "vehicles.id"
    assert fk.ondelete == "SET NULL"


@pytest.mark.unit
def test_match_candidate_pair_uniqueness_and_order_check() -> None:
    expected_pair = frozenset({"listing_a_id", "listing_b_id"})
    assert expected_pair in _unique_column_sets("vehicle_match_candidates")
    checks = _check_constraints("vehicle_match_candidates")
    check_names = {c.name for c in checks}
    assert "ck_vehicle_match_candidates_pair_order" in check_names


@pytest.mark.unit
def test_match_candidate_columns_types() -> None:
    table = _table("vehicle_match_candidates")
    assert isinstance(table.c["match_reasons"].type, JSONB)
    assert isinstance(table.c["confidence_score"].type, Numeric)


@pytest.mark.unit
def test_market_estimates_columns_and_check() -> None:
    table = _table("market_estimates")
    assert isinstance(table.c["estimated_amount"].type, Numeric)
    assert isinstance(table.c["low_amount"].type, Numeric)
    assert isinstance(table.c["high_amount"].type, Numeric)
    assert isinstance(table.c["confidence_score"].type, Numeric)
    checks = _check_constraints("market_estimates")
    check_names = {c.name for c in checks}
    assert "ck_market_estimates_target_present" in check_names
