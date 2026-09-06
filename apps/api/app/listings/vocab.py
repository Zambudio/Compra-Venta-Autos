"""Vocabulario de dominio para anuncios: enumeraciones y canonicalización.

Estas enumeraciones son la representación interna única a la que el normalizador
traduce cualquier payload observado (Plan Maestro §11, ADR-0006).
"""

from __future__ import annotations

from enum import StrEnum


class FuelType(StrEnum):
    PETROL = "PETROL"
    DIESEL = "DIESEL"
    LPG = "LPG"
    CNG = "CNG"
    HYBRID = "HYBRID"
    PLUGIN_HYBRID = "PLUGIN_HYBRID"
    ELECTRIC = "ELECTRIC"
    OTHER = "OTHER"


class Transmission(StrEnum):
    MANUAL = "MANUAL"
    AUTOMATIC = "AUTOMATIC"
    UNKNOWN = "UNKNOWN"


class SellerType(StrEnum):
    PRIVATE = "PRIVATE"
    DEALER = "DEALER"
    UNKNOWN = "UNKNOWN"


class ListingStatus(StrEnum):
    ACTIVE = "ACTIVE"
    WITHDRAWN = "WITHDRAWN"
    UNKNOWN = "UNKNOWN"


class EntryChannel(StrEnum):
    """Cómo entró el anuncio al sistema."""

    MOCK_SYNC = "MOCK_SYNC"
    MANUAL_ENTRY = "MANUAL_ENTRY"


class ProviderKind(StrEnum):
    """Medio de adquisición de una fuente (ADR-0006)."""

    MOCK = "MOCK"
    MANUAL = "MANUAL"
    CONNECTOR = "CONNECTOR"


# --- Canonicalización de marca -------------------------------------------------

# Claves en minúsculas y sin acentos redundantes; el valor es la forma canónica.
BRAND_ALIASES: dict[str, str] = {
    "vw": "Volkswagen",
    "volkswagen": "Volkswagen",
    "seat": "SEAT",
    "cupra": "Cupra",
    "bmw": "BMW",
    "mercedes": "Mercedes-Benz",
    "mercedes benz": "Mercedes-Benz",
    "mercedes-benz": "Mercedes-Benz",
    "merc": "Mercedes-Benz",
    "audi": "Audi",
    "peugeot": "Peugeot",
    "citroen": "Citroën",
    "citroën": "Citroën",
    "renault": "Renault",
    "dacia": "Dacia",
    "opel": "Opel",
    "ford": "Ford",
    "toyota": "Toyota",
    "kia": "Kia",
    "hyundai": "Hyundai",
    "nissan": "Nissan",
    "mazda": "Mazda",
    "honda": "Honda",
    "fiat": "Fiat",
    "skoda": "Škoda",
    "škoda": "Škoda",
    "volvo": "Volvo",
    "mini": "MINI",
    "land rover": "Land Rover",
    "alfa romeo": "Alfa Romeo",
    "suzuki": "Suzuki",
}


def canonical_brand(raw: str) -> str:
    """Devuelve la marca canónica; si no hay alias, capitaliza de forma segura."""

    cleaned = " ".join(raw.split()).strip()
    alias = BRAND_ALIASES.get(cleaned.casefold())
    if alias is not None:
        return alias
    return cleaned.title()


# --- Mapas de alias para enumeraciones ---------------------------------------

_FUEL_ALIASES: dict[str, FuelType] = {
    "gasolina": FuelType.PETROL,
    "petrol": FuelType.PETROL,
    "bencina": FuelType.PETROL,
    "diesel": FuelType.DIESEL,
    "diésel": FuelType.DIESEL,
    "gasoil": FuelType.DIESEL,
    "gasoleo": FuelType.DIESEL,
    "gasóleo": FuelType.DIESEL,
    "glp": FuelType.LPG,
    "lpg": FuelType.LPG,
    "autogas": FuelType.LPG,
    "gnc": FuelType.CNG,
    "cng": FuelType.CNG,
    "gas natural": FuelType.CNG,
    "hibrido": FuelType.HYBRID,
    "híbrido": FuelType.HYBRID,
    "hybrid": FuelType.HYBRID,
    "hibrido enchufable": FuelType.PLUGIN_HYBRID,
    "híbrido enchufable": FuelType.PLUGIN_HYBRID,
    "phev": FuelType.PLUGIN_HYBRID,
    "electrico": FuelType.ELECTRIC,
    "eléctrico": FuelType.ELECTRIC,
    "electric": FuelType.ELECTRIC,
    "ev": FuelType.ELECTRIC,
    "bev": FuelType.ELECTRIC,
}

_TRANSMISSION_ALIASES: dict[str, Transmission] = {
    "manual": Transmission.MANUAL,
    "man": Transmission.MANUAL,
    "automatico": Transmission.AUTOMATIC,
    "automático": Transmission.AUTOMATIC,
    "automatica": Transmission.AUTOMATIC,
    "automática": Transmission.AUTOMATIC,
    "automatic": Transmission.AUTOMATIC,
    "auto": Transmission.AUTOMATIC,
    "cvt": Transmission.AUTOMATIC,
    "dsg": Transmission.AUTOMATIC,
}

_SELLER_ALIASES: dict[str, SellerType] = {
    "particular": SellerType.PRIVATE,
    "private": SellerType.PRIVATE,
    "profesional": SellerType.DEALER,
    "professional": SellerType.DEALER,
    "concesionario": SellerType.DEALER,
    "dealer": SellerType.DEALER,
    "empresa": SellerType.DEALER,
}


def parse_fuel_type(raw: str | None) -> FuelType:
    if raw is None:
        return FuelType.OTHER
    return _FUEL_ALIASES.get(" ".join(raw.split()).casefold(), FuelType.OTHER)


def parse_transmission(raw: str | None) -> Transmission:
    if raw is None:
        return Transmission.UNKNOWN
    return _TRANSMISSION_ALIASES.get(" ".join(raw.split()).casefold(), Transmission.UNKNOWN)


def parse_seller_type(raw: str | None) -> SellerType:
    if raw is None:
        return SellerType.UNKNOWN
    return _SELLER_ALIASES.get(" ".join(raw.split()).casefold(), SellerType.UNKNOWN)
