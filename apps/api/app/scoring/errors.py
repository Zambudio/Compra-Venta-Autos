"""Excepciones de dominio y API para scoring y oportunidades."""

from uuid import UUID

from app.core.errors import APIError


class ScoringProfileNotFoundError(APIError):
    def __init__(self, profile_id_or_slug: UUID | str) -> None:
        super().__init__(
            status_code=404,
            code="scoring/profile-not-found",
            title="Perfil de scoring no encontrado",
            detail=(
                f"No se encontró ningún perfil de scoring con identificador '{profile_id_or_slug}'."
            ),
        )


class ScoringProfileVersionNotFoundError(APIError):
    def __init__(self, version_id: UUID) -> None:
        super().__init__(
            status_code=404,
            code="scoring/version-not-found",
            title="Versión de perfil de scoring no encontrada",
            detail=f"No se encontró la versión de perfil de scoring con ID '{version_id}'.",
        )


class ScoringProfileSlugAlreadyExistsError(APIError):
    def __init__(self, slug: str) -> None:
        super().__init__(
            status_code=409,
            code="scoring/slug-already-exists",
            title="Slug de perfil de scoring ya en uso",
            detail=f"Ya existe un perfil de scoring con el slug '{slug}'.",
        )


class OpportunityNotFoundError(APIError):
    def __init__(self, opportunity_id: UUID) -> None:
        super().__init__(
            status_code=404,
            code="scoring/opportunity-not-found",
            title="Oportunidad no encontrada",
            detail=f"No se encontró la oportunidad con ID '{opportunity_id}'.",
        )


class TargetNotFoundError(APIError):
    def __init__(self, target_type: str, target_id: UUID) -> None:
        super().__init__(
            status_code=404,
            code="scoring/target-not-found",
            title=f"{target_type.capitalize()} no encontrado",
            detail=f"No se encontró el objeto de tipo '{target_type}' con ID '{target_id}'.",
        )
