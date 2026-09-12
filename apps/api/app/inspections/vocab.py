from enum import StrEnum


class InspectionStatus(StrEnum):
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class CheckResult(StrEnum):
    PASS = "PASS"  # noqa: S105
    WARNING = "WARNING"
    FAIL = "FAIL"
    NOT_CHECKED = "NOT_CHECKED"
