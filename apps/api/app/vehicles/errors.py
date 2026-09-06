"""Excepciones de dominio para vehículos y matching."""

from __future__ import annotations

from uuid import UUID


class VehicleNotFoundError(Exception):
    def __init__(self, vehicle_id: UUID) -> None:
        super().__init__(f"Vehicle {vehicle_id} not found")
        self.vehicle_id = vehicle_id


class MatchCandidateNotFoundError(Exception):
    def __init__(self, candidate_id: UUID) -> None:
        super().__init__(f"Match candidate {candidate_id} not found")
        self.candidate_id = candidate_id


class MatchCandidateAlreadyDecidedError(Exception):
    def __init__(self, candidate_id: UUID, status: str) -> None:
        super().__init__(f"Match candidate {candidate_id} is already decided: {status}")
        self.candidate_id = candidate_id
        self.status = status
        self.current_status = status
