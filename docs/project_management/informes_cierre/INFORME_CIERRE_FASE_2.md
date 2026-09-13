# Informe de cierre — Fase 2: Search y Adquisición (Mock / Manual)

**Fecha:** 2026-09-06 · **Rama:** `feature/fase-2-search-adquisicion` ·
**Fuente de verdad operativa:** [`task.md`](task.md) (F2.1–F2.10, todas `[x]`).

Fase autorizada por el usuario. Regla mantenida en todo momento: **cero scraping**;
la única ingesta es `MockConnector` (catálogo local versionado y anonimizado) y
`ManualEntryConnector` (ficha aportada bajo acción humana).

## 1. Alcance entregado

| Área | Entregado |
| --- | --- |
| Contratos de adquisición | `BaseConnector` ABC (`search`/`fetch`/`health_check`), `RawListing`, `ConnectorSearchPage`, `ConnectorHealth`, `ConnectorSearchFilter`, `TransientConnectorError`/`UnknownConnectorError`. |
| Conectores | `MockConnector` (36 anuncios ES en `catalog_v1.json`; filtros marca/modelo/año/precio/combustible/km/provincia/vendedor; paginación; latencia y fallos transitorios deterministas y desactivables). `ManualEntryConnector` (`build_raw`). `registry.py` expone **solo** `mock` y `manual`. |
| Normalización | `normalize(payload, source_key) -> NormalizedListing` puro (Plan Maestro §11): `Decimal` para dinero, enums, alias de marca/combustible/cambio/vendedor, rangos validados, campos no resolubles a `None`. `payload_hash` canónico y estable. |
| Persistencia | `sources`, `source_compliance_reviews`, `source_sync_runs`, `vehicle_listings`, `raw_listing_payloads`, `listing_snapshots`. Migración de esquema `20260906_0002` + migración de datos `20260906_0003` (seed idempotente de `mock`/`manual`). |
| Deduplicación (ADR-0012) | Por `payload_hash` + `(source_id, external_id)`. `RawListingPayload` inmutable. `ListingSnapshot` solo ante cambio de precio, km o hash de descripción. Sin entidad `Vehicle` (Fase 3). |
| API `/api/v1` | `GET /listings` (filtros + paginación), `GET /listings/{id}` (+ snapshots), `POST /listings/manual` (CSRF, `OWNER\|ADMIN`, 409 duplicado). `GET /sources`, `GET /sources/{key}/health`, `POST /sources/{key}/sync` (`mode=sync\|async`), `GET /sources/{key}/sync-runs`. DTOs sin `payload` ni `payload_hash`. |
| Jobs | Actor Dramatiq `sync_source_actor` idempotente por `run_id`; `app/core/broker.py` compartido; reintentos de fallos transitorios; estado `PARTIAL`/`FAILED` con resumen saneado. |
| Frontend | Shell autenticado con pestañas `Anuncios` (por defecto) / `Estado` y navegación por teclado. `listings-view` (filtros RHF+Zod, tarjetas, paginación, botón de sincronización, estados loading/empty/error/success). `manual-listing-form`. `listing-detail` con histórico de snapshots. Primitivos `select`/`field`/`badge`. |
| Contrato | `docs/api/openapi.json` regenerado; CI valida con `git diff --exit-code`. |

**Fuera de Fase 2 (Fase 3+):** entidad `Vehicle`, `VehicleListing.vehicle_id`,
deduplicación entre fuentes, `VehicleMatchCandidate`, `MarketEstimate`.

## 2. Decisiones de arquitectura

- **[ADR-0012](docs/adr/0012-listing-ingestion-and-dedup.md)** (nuevo): ingesta
  inmutable, dedup por hash de payload + identidad de fuente, snapshot-on-change,
  `SourceSyncRun` para observabilidad, sin `Vehicle` hasta Fase 3.
- Semilla de fuentes en **migración de datos separada** del esquema (Plan §38).
- Home post-login pasa a un **shell con pestañas**; `Anuncios` es la landing.
- Sincronización **síncrona por defecto**, `mode=async` opcional vía Dramatiq.

## 3. Calidad y pruebas ejecutadas

| Lane | Resultado |
| --- | --- |
| `ruff format --check` / `ruff check` | Limpio (86 archivos). |
| `mypy --strict` (`app` + `tests`) | Limpio (81 archivos). |
| `pytest -m "not integration"` (backend) | **159 pasan**, cobertura **82.37%** (normalizador y conectores 100%). |
| `pytest -m integration` (PostgreSQL + Redis reales) | 23 tests; se ejecutan en CI (sin Docker en el host de desarrollo). Migraciones validadas además con `alembic upgrade --sql` offline y aplicadas en el PostgreSQL real del NAS. |
| `eslint` / `prettier` / `tsc --noEmit` | Limpio. |
| `vitest` (frontend) | **56 pasan**, cobertura **91.4% stmts / 82.1% branches / 92.9% funcs / 93.5% líneas**; `vitest-axe` sin violaciones en cada pantalla nueva. |
| `next build --webpack` | Compila y genera páginas correctamente. |
| E2E Playwright | `auth.spec.ts` actualizado; `listings.spec.ts` nuevo (login → sincronizar → filtrar → detalle → alta manual → ver anuncio). Se ejecutan en CI sobre el stack Compose. |
| Seguridad | Sin dependencias nuevas; `pip-audit` limpio (deps de `uv.lock`). CodeQL (Python + JS/TS) en verde. Al ejecutarse el pipeline completo por primera vez en `main` aparecieron fallos **preexistentes** (no de Fase 2): E2E nunca había corrido (base URL/WebKit), Semgrep con una regla MEDIUM nueva (`uv-missing-dependency-cooldown`) y Trivy con dos HIGH de copias vendorizadas por `pip` en la imagen base. **Todos corregidos** en el cierre de Fase 2 (ver `implementation_plan.md → Fallos de CI detectados y corregidos`). |

## 4. Validación en vivo (NAS `192.168.1.3:3080`)

Reconstrucción `docker-compose build api web worker` + `up -d`: **6 contenedores
_healthy_** (`caddy`, `web`, `api`, `worker`, `postgres`, `redis`).

Migraciones aplicadas en `motorscope-postgres-1` (PostgreSQL 18):
`20260906_0001 → 0002 → 0003 (head)`, sin errores.

Smoke test a través de Caddy:

| Comprobación | Resultado |
| --- | --- |
| `GET /health/live` · `/health/ready` | 200 · 200 |
| `POST /auth/login` (OWNER) | 200, cookie de sesión + CSRF |
| `GET /sources` | `["manual", "mock"]`, `automated_allowed: true` |
| `POST /sources/mock/sync` | `SUCCESS`, 36 creados / 36 vistos |
| `GET /listings?sort=price_asc` | total 36; más barato Peugeot 206 1500.00 €; DTO sin `payload` |
| `POST /listings/manual` | 201 |
| `POST /listings/manual` (repetido) | 409 `listing_already_exists` |
| `POST /sources/mock/sync` (repetido) | `SUCCESS`, 0 creados / 0 actualizados (idempotente) |
| `POST /sources/mock/sync` sin `X-CSRF-Token` | 403 |
| `GET /sources/mock/sync-runs` | `["SUCCESS", "SUCCESS"]` |
| `GET /listings/{id}` | detalle con snapshots; DTO sin `payload`/`payload_hash` |
| `GET /` (web) | 200 |

Datos de prueba manuales eliminados tras el smoke test; el catálogo Mock (36
anuncios deterministas) se conserva para exploración.

## 5. Riesgos y pendientes

- **R-02 (Docker no disponible en el host de desarrollo):** los tests de
  integración y E2E no se ejecutan localmente; se validan en CI y en el NAS. Las
  migraciones se validaron adicionalmente contra PostgreSQL real.
- **R-03 (datos personales):** la entrada manual no persiste matrículas ni
  teléfonos; `province`/`location` son texto libre opcional. Revisión de privacidad
  detallada sigue pendiente antes de incorporar datos de fuentes reales.
- **Cobertura de integración local:** algunos módulos con lógica muy ligada a la
  base de datos (`app/sources/service.py`) muestran cobertura baja en la suite
  unitaria local; su ruta completa la cubren los tests de integración en CI.
- **`app/core/broker.py`:** conecta a Redis de forma perezosa; el worker importa
  `app/sources/tasks` para registrar el actor.
- **CI:** este cierre es el primer pipeline completo verde en `main` (los jobs
  `frontend`/`e2e` no llegaban a ejecutarse antes). Cambios de infraestructura
  aplicados: orden `pnpm/action-setup` → `setup-node`; `exclude-newer` de uv;
  `pip` fuera de la imagen runtime; base URL y navegador de Playwright en CI.

## 6. Siguiente fase propuesta

**Fase 3 — Vehicles y Market Data** (requiere aprobación explícita del usuario):
entidad `Vehicle`, `VehicleListing.vehicle_id` nullable, deduplicación asistida
entre fuentes (`VehicleMatchCandidate` con confianza y revisión humana),
comparables y `MarketEstimate` con intervalos y nivel de confianza.

No se inicia la Fase 3 sin aprobación explícita.
