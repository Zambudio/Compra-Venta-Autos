"""Seed the fixed Mock and Manual sources and their compliance reviews.

Revision ID: 20260906_0003
Revises: 20260906_0002
Create Date: 2026-09-06

Data migration kept separate from the schema migration (Plan Maestro §38).
Idempotent: re-running leaves the same rows. ``downgrade`` removes both sources
(cascading to their reviews and any listings). Values mirror
``docs/source-compliance.md``. Fixed source ids:

- mock:   11111111-1111-1111-1111-111111111111
- manual: 22222222-2222-2222-2222-222222222222
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260906_0003"
down_revision: str | None = "20260906_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_INSERT_SOURCES = """
INSERT INTO sources (id, key, name, provider_kind, is_active, is_automatable, created_at, updated_at)
VALUES
    ('11111111-1111-1111-1111-111111111111'::uuid, 'mock', 'Catálogo Mock', 'MOCK', true, true,
     now(), now()),
    ('22222222-2222-2222-2222-222222222222'::uuid, 'manual', 'Entrada manual', 'MANUAL', true, true,
     now(), now())
ON CONFLICT (key) DO NOTHING
"""

_CLEAR_REVIEWS = """
DELETE FROM source_compliance_reviews
WHERE source_id IN ('11111111-1111-1111-1111-111111111111'::uuid,
                    '22222222-2222-2222-2222-222222222222'::uuid)
"""

_INSERT_REVIEWS = """
INSERT INTO source_compliance_reviews
    (id, source_id, acquisition_method, automated_allowed, authentication_required,
     rate_limit, terms_url, checked_at, notes, created_at)
VALUES
    (gen_random_uuid(), '11111111-1111-1111-1111-111111111111'::uuid,
     'fixture local versionada y anonimizada', true, 'No',
     NULL, NULL, '2026-09-06T00:00:00+00:00'::timestamptz,
     'Única fuente automática prevista para tests normales.', now()),
    (gen_random_uuid(), '22222222-2222-2222-2222-222222222222'::uuid,
     'formulario/archivo aportado por usuario', true, 'App privada',
     'límites de app', NULL, '2026-09-06T00:00:00+00:00'::timestamptz,
     'Validar procedencia, minimización, copyright, tamaño y contenido antes de persistir.', now())
"""

_DELETE_SOURCES = """
DELETE FROM sources
WHERE id IN ('11111111-1111-1111-1111-111111111111'::uuid,
             '22222222-2222-2222-2222-222222222222'::uuid)
"""


def upgrade() -> None:
    op.execute(_INSERT_SOURCES)
    op.execute(_CLEAR_REVIEWS)
    op.execute(_INSERT_REVIEWS)


def downgrade() -> None:
    op.execute(_DELETE_SOURCES)
