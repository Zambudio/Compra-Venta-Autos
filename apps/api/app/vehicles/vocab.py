"""Vocabulario controlado y enums del dominio de vehículos y estimaciones."""

from enum import StrEnum


class MatchCandidateStatus(StrEnum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"


class MarketEstimateMethod(StrEnum):
    COMPARABLES_MEDIAN_IQR = "COMPARABLES_MEDIAN_IQR"
