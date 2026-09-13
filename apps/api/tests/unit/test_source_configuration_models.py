from __future__ import annotations

import app.models  # noqa: F401
import pytest
from app.core.models import Base
from app.sources.models import SourceConfig, SourceConfigChange

pytestmark = pytest.mark.unit


def test_source_configuration_tables_are_registered_with_required_constraints() -> None:
    configurations = Base.metadata.tables["source_configurations"]
    changes = Base.metadata.tables["source_config_changes"]

    assert configurations.c.source_key.unique is True
    assert configurations.c.source_key.foreign_keys
    assert configurations.c.enabled.nullable is False
    assert configurations.c.config.nullable is False
    assert changes.c.source_key.foreign_keys
    assert changes.c.changed_by.foreign_keys
    assert {index.name for index in changes.indexes} >= {
        "ix_source_config_changes_source_changed"
    }


def test_source_configuration_uses_safe_application_defaults() -> None:
    change = SourceConfigChange(
        source_key="wallapop",
        before={"enabled": True, "config": {}},
        after={"enabled": False, "config": {}},
    )

    assert SourceConfig.__table__.c.enabled.default.arg is True
    assert SourceConfig.__table__.c.config.default.arg(None) == {}
    assert change.before["enabled"] is True
    assert change.after["enabled"] is False
