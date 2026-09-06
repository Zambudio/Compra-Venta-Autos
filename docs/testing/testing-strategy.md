# Estrategia de testing

Fecha: 2026-09-06.

## Principios

Pirámide: unit → integration → contract/component → E2E → security. Tests deterministas, independientes y orientados a comportamiento. La suite normal no llama fuentes reales. PostgreSQL no se sustituye por SQLite cuando se prueba persistencia, constraints o migraciones.

## Capas

| Capa                | Herramientas                             | Objetivo Foundation                                        |
| ------------------- | ---------------------------------------- | ---------------------------------------------------------- |
| Unit backend        | pytest, pytest-asyncio                   | configuración, auth crypto, CSRF, errores y utilidades     |
| Integration backend | pytest + PostgreSQL/Redis reales         | migraciones, sesiones, login/logout, rate limit, readiness |
| Contract/API        | httpx ASGI + OpenAPI                     | esquemas, errores, headers y compatibilidad                |
| Component frontend  | Vitest, Testing Library, user-event, axe | formulario accesible y estados visibles                    |
| E2E                 | Playwright                               | login → estado → logout en Compose                         |
| Security            | Semgrep, Gitleaks, audit, Trivy, CodeQL  | código, secretos, dependencias e imágenes                  |

## TDD y fixtures

Se sigue red → verde → refactor. Reloj, generador aleatorio y stores pueden inyectarse en unit tests; las fixtures no contienen PII real. Integración crea un usuario por test/worker y limpia en transacción o schema dedicado. Las respuestas futuras de portales serán anonimizadas, versionadas y legales.

## Cobertura

Umbral inicial global backend/frontend: 80% líneas/statements, 75% branches, 80% funciones. Autenticación/autorización, scoring, finanzas, normalizadores, deduplicación y estados aspiran a 100% de ramas significativas. Los umbrales crecen por fase; no se persigue cobertura vacía.

Mutation testing se evaluará en Fase 5 y Fase 7 para score y finanzas; resultado/decisión se documentará.

## Matriz Foundation

- Settings: entornos válidos y rechazo de secretos/orígenes inseguros en producción.
- Health: liveness independiente; readiness 200/503 según PostgreSQL/Redis.
- Middleware: request ID válido/nuevo, headers y error genérico.
- Auth: usuario válido/inválido/inactivo, hash y rehash, cookie flags, expiración, revocación, CSRF ausente/incorrecto/correcto, roles y rate limit.
- Migraciones: base vacía `upgrade head`; `downgrade base`; `upgrade head`; schema esperado.
- Frontend: labels, validación, loading, credenciales inválidas, éxito, sesión existente, logout, teclado y axe.
- E2E: entorno Compose real y cookies de navegador.

## Matriz Fase 2 (Search y adquisición)

- **Normalizador** (`test_normalizer.py`, ~53 casos): mapeo de campos, alias de
  marca/combustible/cambio/vendedor, `Decimal` para dinero, rangos inválidos,
  campos ausentes → `None`, estabilidad de `payload_hash` ante reordenación.
- **Conectores** (`test_mock_connector.py`, `test_manual_connector.py`,
  `test_connector_registry.py`): determinismo del catálogo, filtros, paginación,
  `has_more`, latencia desactivable, `TransientConnectorError` determinista,
  `health_check`, registro solo `mock`+`manual`.
- **Ingesta** (`test_listing_service.py`): `decide_ingest` puro (crear/seen/
  actualizar, snapshot solo ante cambio), canal de entrada, `search`/`get_detail`.
- **Fuentes** (`test_sources_service.py`): `_final_status`, `_sanitize`,
  reintentos de `_search_with_retry`, health por registro.
- **Endpoints** (`test_sources_endpoints.py`, `test_listings_endpoints.py`):
  200/404/409, CSRF, roles (`VIEWER` → 403), DTOs sin `payload` ni `payload_hash`.
- **Integración PostgreSQL real** (CI): `test_migration_0002` (base→head, head→0001→
  head, seed idempotente); `test_ingestion_flow` (sync completo, re-sync sin
  duplicados, cambio de precio → snapshot); `test_sync_api`, `test_listings_api`,
  `test_manual_listing_api`.
- **Contrato**: `export_openapi.py` regenera `docs/api/openapi.json`; CI hace
  `git diff --exit-code`.
- **Frontend** (Vitest + Testing Library + `vitest-axe`): estados loading/empty/
  error/success de `listings-view`, filtros, paginación, sync; validación y envío
  de `manual-listing-form` (incluye 409); histórico de snapshots en
  `listing-detail`; navegación por teclado del shell; `axe` sin violaciones en
  cada pantalla nueva.
- **E2E** (`listings.spec.ts`): login → sincronizar Mock → filtrar → ver detalle
  → alta manual → ver el anuncio nuevo en la lista.

## Comandos y lanes

```powershell
uv run --project apps/api ruff format --check .
uv run --project apps/api ruff check .
uv run --project apps/api mypy app tests
uv run --project apps/api pytest -m "not integration" --cov
uv run --project apps/api pytest -m integration
pnpm lint
pnpm format:check
pnpm typecheck
pnpm test
pnpm e2e
```

CI levanta PostgreSQL y Redis como servicios, prueba migraciones y ejecuta E2E sobre el stack. Los tests marcados `integration` deben fallar claramente si la infraestructura no existe, no caer silenciosamente a SQLite.

## Definition of Done

Todos los lanes aplicables pasan; no hay skips injustificados; migraciones probadas; OpenAPI validado; seguridad sin HIGH/CRITICAL abiertos; documentación/ADRs/task actualizados. Un lane no ejecutado se registra como pendiente o bloqueado.
