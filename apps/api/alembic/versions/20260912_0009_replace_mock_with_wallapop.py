"""Replace Mock connector with Wallapop for production.

Revision ID: 20260912_0009
Revises: 20260912_0008
Create Date: 2026-09-12

Phase 10 requirement: Remove Mock connector and integrate Wallapop as the real
connector for market data acquisition (ADR-0006, Plan Maestro §39).

Data migration approach:
  - Deactivate the mock source (preserves historical listings for audit).
  - Create wallapop source with appropriate compliance.
  - Preserve manual source unchanged.

Idempotent: re-running leaves the same rows.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260912_0009"
down_revision: str | None = "20260912_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DEACTIVATE_MOCK = """
UPDATE sources
SET is_active = false, updated_at = now()
WHERE key = 'mock'
"""

_REMOVE_MOCK_COMPLIANCE = """
DELETE FROM source_compliance_reviews
WHERE source_id = '11111111-1111-1111-1111-111111111111'::uuid
"""

_INSERT_WALLAPOP = """
INSERT INTO sources (id, key, name, provider_kind, is_active, is_automatable, created_at, updated_at)
VALUES ('33333333-3333-3333-3333-333333333333'::uuid, 'wallapop', 'Wallapop', 'CONNECTOR', true, true,
        now(), now())
ON CONFLICT (key) DO NOTHING
"""

_INSERT_WALLAPOP_COMPLIANCE = """
INSERT INTO source_compliance_reviews
    (id, source_id, acquisition_method, automated_allowed, authentication_required,
     rate_limit, terms_url, checked_at, notes, created_at)
VALUES
    (gen_random_uuid(), '33333333-3333-3333-3333-333333333333'::uuid,
     'API no oficial (inofficial but documented)',
     true, 'No',
     'Cloudfront anti-bot + rate limiting; health_check monitors for 403/429',
     'https://www.wallapop.com/terms',
     now()::timestamptz,
     'Wallapop protects its API with anti-bot measures. Respect rate limits and User-Agent headers. Integration authorized per Plan Maestro §41.',
     now())
"""

_REACTIVATE_MOCK = """
UPDATE sources
SET is_active = true, updated_at = now()
WHERE key = 'mock'
"""

_RESTORE_MOCK_COMPLIANCE = """
INSERT INTO source_compliance_reviews
    (id, source_id, acquisition_method, automated_allowed, authentication_required,
     rate_limit, terms_url, checked_at, notes, created_at)
VALUES
    (gen_random_uuid(), '11111111-1111-1111-1111-111111111111'::uuid,
     'fixture local versionada y anonimizada',
     true, 'No',
     NULL,
     NULL,
     '2026-09-06T00:00:00+00:00'::timestamptz,
     'Única fuente automática prevista para tests normales.',
     now())
"""

_REMOVE_WALLAPOP = """
DELETE FROM sources WHERE key = 'wallapop'
"""


def upgrade() -> None:
    op.execute(_DEACTIVATE_MOCK)
    op.execute(_REMOVE_MOCK_COMPLIANCE)
    op.execute(_INSERT_WALLAPOP)
    op.execute(_INSERT_WALLAPOP_COMPLIANCE)


def downgrade() -> None:
    op.execute(_REMOVE_WALLAPOP)
    op.execute(_REACTIVATE_MOCK)
    op.execute(_RESTORE_MOCK_COMPLIANCE)
