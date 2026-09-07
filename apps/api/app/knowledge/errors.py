"""Excepciones de dominio para Knowledge Base."""

from __future__ import annotations

from uuid import UUID


class KnowledgeDomainError(Exception):
    """Clase base para errores de Knowledge Base."""


class ManufacturerNotFoundError(KnowledgeDomainError):
    def __init__(self, manufacturer_id: UUID | str) -> None:
        super().__init__(f"Fabricante '{manufacturer_id}' no encontrado.")
        self.manufacturer_id = manufacturer_id


class VehicleModelNotFoundError(KnowledgeDomainError):
    def __init__(self, model_id: UUID | str) -> None:
        super().__init__(f"Modelo de vehículo '{model_id}' no encontrado.")
        self.model_id = model_id


class VehicleGenerationNotFoundError(KnowledgeDomainError):
    def __init__(self, generation_id: UUID | str) -> None:
        super().__init__(f"Generación de vehículo '{generation_id}' no encontrada.")
        self.generation_id = generation_id


class EngineNotFoundError(KnowledgeDomainError):
    def __init__(self, engine_id: UUID | str) -> None:
        super().__init__(f"Motor '{engine_id}' no encontrado.")
        self.engine_id = engine_id


class EngineVariantNotFoundError(KnowledgeDomainError):
    def __init__(self, variant_id: UUID | str) -> None:
        super().__init__(f"Variante de motor '{variant_id}' no encontrada.")
        self.variant_id = variant_id


class TransmissionSpecNotFoundError(KnowledgeDomainError):
    def __init__(self, transmission_id: UUID | str) -> None:
        super().__init__(f"Especificación de transmisión '{transmission_id}' no encontrada.")
        self.transmission_id = transmission_id


class KnowledgeSourceNotFoundError(KnowledgeDomainError):
    def __init__(self, source_id: UUID | str) -> None:
        super().__init__(f"Fuente de conocimiento '{source_id}' no encontrada.")
        self.source_id = source_id


class EvidenceNotFoundError(KnowledgeDomainError):
    def __init__(self, evidence_id: UUID | str) -> None:
        super().__init__(f"Evidencia '{evidence_id}' no encontrada.")
        self.evidence_id = evidence_id


class KnownIssueNotFoundError(KnowledgeDomainError):
    def __init__(self, issue_id: UUID | str) -> None:
        super().__init__(f"Problema conocido '{issue_id}' no encontrado.")
        self.issue_id = issue_id


class VehicleClassificationNotFoundError(KnowledgeDomainError):
    def __init__(self, classification_id: UUID | str) -> None:
        super().__init__(f"Clasificación '{classification_id}' no encontrada.")
        self.classification_id = classification_id


class IssueCannotBeVerifiedWithoutEvidenceError(KnowledgeDomainError):
    """Plan Maestro §15: no permitir que una afirmación mecánica exista sin evidencias trazables."""

    def __init__(self, issue_id: UUID | str) -> None:
        super().__init__(
            f"El problema mecánico '{issue_id}' no puede marcarse como VERIFIED "
            "sin evidencias trazables asociadas."
        )
        self.issue_id = issue_id
