"""Vocabularios y enums del dominio Knowledge Base."""

from __future__ import annotations

from enum import StrEnum


class SourceTrustLevel(StrEnum):
    """Niveles de confianza de fuentes según Plan Maestro §15."""

    A = "A"  # Oficial: fabricantes, DGT, Safety Gate UE, campañas oficiales
    B = "B"  # Estadística: ADAC, TÜV, asociaciones de consumidores
    C = "C"  # Especializada: prensa técnica, talleres y canales mecánicos reconocidos
    D = "D"  # Comunidad: foros, Reddit, YouTube, grupos de propietarios


class KnowledgeSourceType(StrEnum):
    """Tipos de fuentes de conocimiento."""

    OFFICIAL_RECALL = "OFFICIAL_RECALL"
    STATISTICAL_REPORT = "STATISTICAL_REPORT"
    TECHNICAL_MEDIA = "TECHNICAL_MEDIA"
    WORKSHOP_NOTE = "WORKSHOP_NOTE"
    COMMUNITY_REPORT = "COMMUNITY_REPORT"


class IssueSeverity(StrEnum):
    """Nivel de severidad de un problema mecánico."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IssueFrequency(StrEnum):
    """Frecuencia estimada de aparición de una avería."""

    RARE = "RARE"
    OCCASIONAL = "OCCASIONAL"
    FREQUENT = "FREQUENT"
    SYSTEMIC = "SYSTEMIC"


class IssueStatus(StrEnum):
    """Estado del ciclo de vida del problema en la Wiki (Plan Maestro §16)."""

    DRAFT = "DRAFT"
    REVIEWED = "REVIEWED"
    VERIFIED = "VERIFIED"
    DEPRECATED = "DEPRECATED"


class VehicleComponent(StrEnum):
    """Subsistema o componente mecánico afectado."""

    ENGINE_INTERNAL = "ENGINE_INTERNAL"
    TIMING_SYSTEM = "TIMING_SYSTEM"
    TURBOCHARGER = "TURBOCHARGER"
    FUEL_SYSTEM = "FUEL_SYSTEM"
    EMISSIONS_EGR_DPF = "EMISSIONS_EGR_DPF"
    COOLING_SYSTEM = "COOLING_SYSTEM"
    TRANSMISSION_MANUAL = "TRANSMISSION_MANUAL"
    TRANSMISSION_AUTOMATIC = "TRANSMISSION_AUTOMATIC"
    CLUTCH_FLYWHEEL = "CLUTCH_FLYWHEEL"
    ELECTRICAL = "ELECTRICAL"
    SUSPENSION_STEERING = "SUSPENSION_STEERING"
    BRAKES = "BRAKES"
    BODYWORK = "BODYWORK"
    OTHER = "OTHER"


class ClassificationStatus(StrEnum):
    """Estado de clasificación de fiabilidad (Plan Maestro §17)."""

    WHITELIST = "WHITELIST"
    WATCHLIST = "WATCHLIST"
    BLACKLIST = "BLACKLIST"
    UNKNOWN = "UNKNOWN"


class ClassificationTargetType(StrEnum):
    """Ámbito al que aplica la clasificación."""

    MODEL = "MODEL"
    GENERATION = "GENERATION"
    ENGINE = "ENGINE"
    ENGINE_VARIANT = "ENGINE_VARIANT"
    TRANSMISSION = "TRANSMISSION"
    COMBINATION = "COMBINATION"


class TransmissionType(StrEnum):
    """Tipo técnico de transmisión."""

    MANUAL = "MANUAL"
    AUTOMATIC_TORQUE_CONVERTER = "AUTOMATIC_TORQUE_CONVERTER"
    DUAL_CLUTCH = "DUAL_CLUTCH"
    CVT = "CVT"
    AUTOMATED_MANUAL = "AUTOMATED_MANUAL"
    UNKNOWN = "UNKNOWN"


class EngineAspiration(StrEnum):
    """Tipo de aspiración del motor."""

    NATURALLY_ASPIRATED = "NATURALLY_ASPIRATED"
    TURBOCHARGED = "TURBOCHARGED"
    SUPERCHARGED = "SUPERCHARGED"
    TWINCHARGED = "TWINCHARGED"
    OTHER = "OTHER"
