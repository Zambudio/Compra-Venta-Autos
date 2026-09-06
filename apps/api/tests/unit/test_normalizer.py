from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from app.listings.normalizer import NormalizationError, normalize, payload_hash
from app.listings.vocab import FuelType, SellerType, Transmission


def _payload(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "external_id": "mock-0001",
        "url": "https://mock.motorscope.local/anuncio/mock-0001",
        "titulo": "SEAT Ibiza 1.4 TDI Reference",
        "marca": "Seat",
        "modelo": "Ibiza",
        "version": "1.4 TDI Reference",
        "generacion": "6J",
        "anio": 2013,
        "km": 168000,
        "precio": 2800,
        "moneda": "EUR",
        "combustible": "Diésel",
        "cambio": "Manual",
        "potencia_cv": 90,
        "codigo_motor": "CAYC",
        "provincia": "Murcia",
        "poblacion": "Cartagena",
        "vendedor": "particular",
        "descripcion": "Coche en buen estado, distribución hecha.",
        "fotos": ["https://mock.motorscope.local/img/0001-1.jpg"],
        "publicado": "2026-08-20",
    }
    base.update(overrides)
    return base


@pytest.mark.unit
def test_normalize_maps_core_fields() -> None:
    result = normalize(_payload(), source_key="mock")

    assert result.source_key == "mock"
    assert result.external_id == "mock-0001"
    assert result.brand == "SEAT"
    assert result.model == "Ibiza"
    assert result.trim == "1.4 TDI Reference"
    assert result.generation == "6J"
    assert result.engine_code == "CAYC"
    assert result.year == 2013
    assert result.mileage_km == 168000
    assert result.fuel_type is FuelType.DIESEL
    assert result.transmission is Transmission.MANUAL
    assert result.seller_type is SellerType.PRIVATE
    assert result.province == "Murcia"
    assert result.location == "Cartagena"
    assert result.image_urls == ["https://mock.motorscope.local/img/0001-1.jpg"]


@pytest.mark.unit
def test_normalize_price_is_decimal_with_currency() -> None:
    result = normalize(_payload(precio=2800), source_key="mock")

    assert result.price_amount == Decimal("2800")
    assert isinstance(result.price_amount, Decimal)
    assert result.price_currency == "EUR"


@pytest.mark.unit
def test_normalize_defaults_currency_to_eur() -> None:
    payload = _payload()
    del payload["moneda"]

    assert normalize(payload, source_key="mock").price_currency == "EUR"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("vw", "Volkswagen"),
        ("Volkswagen", "Volkswagen"),
        ("seat", "SEAT"),
        ("Mercedes Benz", "Mercedes-Benz"),
        ("citroen", "Citroën"),
        ("Kia", "Kia"),
    ],
)
def test_normalize_canonicalizes_brand(raw: str, expected: str) -> None:
    assert normalize(_payload(marca=raw), source_key="mock").brand == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Diésel", FuelType.DIESEL),
        ("gasoil", FuelType.DIESEL),
        ("Gasolina", FuelType.PETROL),
        ("GLP", FuelType.LPG),
        ("Híbrido", FuelType.HYBRID),
        ("Híbrido enchufable", FuelType.PLUGIN_HYBRID),
        ("Eléctrico", FuelType.ELECTRIC),
        ("plasma", FuelType.OTHER),
    ],
)
def test_normalize_maps_fuel_aliases(raw: str, expected: FuelType) -> None:
    assert normalize(_payload(combustible=raw), source_key="mock").fuel_type is expected


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Manual", Transmission.MANUAL),
        ("Automático", Transmission.AUTOMATIC),
        ("automatica", Transmission.AUTOMATIC),
        ("otra cosa", Transmission.UNKNOWN),
    ],
)
def test_normalize_maps_transmission_aliases(raw: str, expected: Transmission) -> None:
    assert normalize(_payload(cambio=raw), source_key="mock").transmission is expected


@pytest.mark.unit
def test_normalize_transmission_missing_is_unknown() -> None:
    payload = _payload()
    del payload["cambio"]

    assert normalize(payload, source_key="mock").transmission is Transmission.UNKNOWN


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("particular", SellerType.PRIVATE),
        ("profesional", SellerType.DEALER),
        ("concesionario", SellerType.DEALER),
        ("", SellerType.UNKNOWN),
    ],
)
def test_normalize_maps_seller_type(raw: str, expected: SellerType) -> None:
    assert normalize(_payload(vendedor=raw), source_key="mock").seller_type is expected


@pytest.mark.unit
def test_normalize_converts_cv_to_kw() -> None:
    assert normalize(_payload(potencia_cv=90), source_key="mock").power_kw == 66


@pytest.mark.unit
def test_normalize_optional_fields_absent_become_none() -> None:
    payload = {
        "external_id": "mock-0002",
        "marca": "Dacia",
        "modelo": "Sandero",
        "anio": 2016,
        "km": 90000,
        "precio": 5200,
        "combustible": "Gasolina",
        "vendedor": "particular",
    }

    result = normalize(payload, source_key="mock")

    assert result.url is None
    assert result.generation is None
    assert result.trim is None
    assert result.engine_code is None
    assert result.power_kw is None
    assert result.location is None
    assert result.description is None
    assert result.published_at is None
    assert result.image_urls == []


@pytest.mark.unit
def test_normalize_parses_published_date_as_utc() -> None:
    result = normalize(_payload(publicado="2026-08-20"), source_key="mock")

    assert result.published_at == datetime(2026, 8, 20, tzinfo=UTC)


@pytest.mark.unit
def test_normalize_trims_whitespace() -> None:
    result = normalize(_payload(modelo="  Ibiza  ", marca=" Seat "), source_key="mock")

    assert result.model == "Ibiza"
    assert result.brand == "SEAT"


@pytest.mark.unit
@pytest.mark.parametrize("missing", ["marca", "modelo", "anio", "km", "precio"])
def test_normalize_rejects_missing_required_field(missing: str) -> None:
    payload = _payload()
    del payload[missing]

    with pytest.raises(NormalizationError):
        normalize(payload, source_key="mock")


@pytest.mark.unit
@pytest.mark.parametrize("year", [1800, 1949, datetime.now(UTC).year + 2])
def test_normalize_rejects_out_of_range_year(year: int) -> None:
    with pytest.raises(NormalizationError):
        normalize(_payload(anio=year), source_key="mock")


@pytest.mark.unit
@pytest.mark.parametrize(("field", "value"), [("km", -1), ("precio", 0), ("precio", -100)])
def test_normalize_rejects_non_positive_numbers(field: str, value: int) -> None:
    with pytest.raises(NormalizationError):
        normalize(_payload(**{field: value}), source_key="mock")


@pytest.mark.unit
def test_normalize_rejects_unparseable_number() -> None:
    with pytest.raises(NormalizationError):
        normalize(_payload(precio="dos mil"), source_key="mock")


@pytest.mark.unit
def test_payload_hash_is_stable_across_key_order() -> None:
    a = {"marca": "Seat", "modelo": "Ibiza", "precio": 2800}
    b = {"precio": 2800, "modelo": "Ibiza", "marca": "Seat"}

    assert payload_hash(a) == payload_hash(b)
    assert len(payload_hash(a)) == 64


@pytest.mark.unit
def test_payload_hash_changes_with_value() -> None:
    a = {"marca": "Seat", "precio": 2800}
    b = {"marca": "Seat", "precio": 2700}

    assert payload_hash(a) != payload_hash(b)


@pytest.mark.unit
def test_payload_hash_handles_nested_and_lists() -> None:
    a = {"fotos": ["1", "2"], "extra": {"x": 1, "y": 2}}
    b = {"extra": {"y": 2, "x": 1}, "fotos": ["1", "2"]}

    assert payload_hash(a) == payload_hash(b)


@pytest.mark.unit
def test_normalize_unknown_brand_is_title_cased() -> None:
    assert normalize(_payload(marca="fabricante raro"), source_key="mock").brand == "Fabricante Raro"


@pytest.mark.unit
def test_normalize_unparseable_date_becomes_none() -> None:
    assert normalize(_payload(publicado="ayer"), source_key="mock").published_at is None


@pytest.mark.unit
def test_normalize_photos_not_a_list_is_empty() -> None:
    assert normalize(_payload(fotos="una-sola-foto.jpg"), source_key="mock").image_urls == []


@pytest.mark.unit
def test_normalize_rejects_unparseable_year() -> None:
    with pytest.raises(NormalizationError):
        normalize(_payload(anio="dos mil trece"), source_key="mock")
