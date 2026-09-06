from __future__ import annotations

import pytest
from app.connectors.base import BaseConnector
from app.connectors.errors import UnknownConnectorError
from app.connectors.registry import available_source_keys, get_connector

pytestmark = pytest.mark.unit


def test_registry_exposes_only_mock_and_manual() -> None:
    assert set(available_source_keys()) == {"mock", "manual"}


@pytest.mark.parametrize("key", ["mock", "manual"])
def test_get_connector_returns_a_base_connector(key: str) -> None:
    connector = get_connector(key)

    assert isinstance(connector, BaseConnector)
    assert connector.source_key == key


def test_get_connector_rejects_unknown_source() -> None:
    with pytest.raises(UnknownConnectorError):
        get_connector("wallapop")
