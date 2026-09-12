# Estado operativo del proyecto

Fuente operativa de verdad. Última actualización: 2026-09-12 (auditoría posterior al cierre de Fase 5).

Estados: `[ ]` pendiente · `[~]` en progreso · `[x]` completado · `[!]` bloqueado.

## Resumen ejecutivo

- **Completado:** Fases 0–5. El producto cubre login, adquisición Mock/Manual,
  normalización, vehículos, históricos, comparables, Knowledge Base, scoring
  determinista y mesa de oportunidades. La última migración desplegada es
  `20260909_0006_scoring_and_opportunities.py`.
- **Despliegue verificado:** stack de 6 contenedores en Synology NAS y smoke de Fase 5
  registrado como 9/9 en `INFORME_CIERRE_FASE_5.md`.
- **Estado reproducible 2026-09-12:** backend 254/254 unit tests, cobertura 85,42%;
  frontend 109/109 tests, cobertura de ramas 72,81% (el gate exige 75%). TypeScript
  estricto pasa. CI de `main` está rojo por formato backend/frontend; además quedan
  incidencias de Ruff, mypy, ESLint y Trivy sobre la imagen web.
- **Siguiente unidad de trabajo:** F6.0, saneamiento del baseline. Después, Fase 6
  Watchlist e Inspección. No se considera iniciada ninguna tarea funcional de Fase 6.

## Fase 0 — Inspección y planning

### [x] F0.1 — Inspeccionar el repositorio

- **Objetivo:** conocer el punto de partida antes de diseñar o implementar.
- **Alcance:** inventario completo, estado Git, instrucciones locales, código, dependencias y artefactos reutilizables.
- **Dependencias:** lectura íntegra de `PLAN_MAESTRO_VEHICULOS_SEGUNDA_MANO.md`.
- **Criterios de aceptación:** inventario reproducible y conflictos/reutilización documentados.
- **Pruebas necesarias:** `rg --files -uu`, inspección de raíz y `git status`.
- **Documentación afectada:** `implementation_plan.md`, `docs/architecture/architecture.md`.
- **Resultado:** solo existía el Plan Maestro; no había Git, código, configuración ni instrucciones `AGENTS.md`. No existe código reutilizable ni conflicto de legado.

### [x] F0.2 — Confirmar alcance, arquitectura y roadmap

- **Objetivo:** convertir el Plan Maestro en un plan ejecutable por fases.
- **Alcance:** MVP, vertical slice, exclusiones, dependencias y gates de fase.
- **Dependencias:** F0.1.
- **Criterios de aceptación:** `implementation_plan.md` y `roadmap.md` separan MVP/V2/V3 y prohíben avance automático.
- **Pruebas necesarias:** revisión documental contra secciones 53–60 del Plan Maestro.
- **Documentación afectada:** `implementation_plan.md`, `roadmap.md`.

### [x] F0.3 — Verificar y fijar versiones estables

- **Objetivo:** seleccionar versiones estables, compatibles y reproducibles.
- **Alcance:** runtimes, dependencias directas, imágenes y gestores de paquetes.
- **Dependencias:** F0.1.
- **Criterios de aceptación:** fuentes oficiales consultadas; versiones sin beta/RC; dependencias directas fijadas; lockfiles generados.
- **Pruebas necesarias:** resolución de `uv.lock`, `pnpm-lock.yaml`, instalación congelada y auditorías.
- **Documentación afectada:** `README.md`, ADR-0011, `docs/architecture/architecture.md`.

### [x] F0.4 — Crear documentación inicial obligatoria

- **Objetivo:** documentar arquitectura, flujos, dominio, seguridad, pruebas, fuentes y operaciones antes del producto.
- **Alcance:** todos los documentos exigidos por la sección 50.
- **Dependencias:** F0.2 y F0.3.
- **Criterios de aceptación:** documentos presentes, coherentes entre sí y con responsables/pendientes explícitos.
- **Pruebas necesarias:** comprobación de enlaces y revisión de consistencia.
- **Documentación afectada:** `README.md`, `SECURITY.md`, `docs/**`.

### [x] F0.5 — Registrar ADRs iniciales

- **Objetivo:** hacer auditables las decisiones arquitectónicas obligatorias.
- **Alcance:** los diez ADRs mínimos y la estrategia de tooling/versionado.
- **Dependencias:** F0.2 y F0.3.
- **Criterios de aceptación:** cada ADR contiene contexto, decisión, alternativas, consecuencias, estado y fecha.
- **Pruebas necesarias:** revisión documental y cruce con implementación.
- **Documentación afectada:** `docs/adr/**`.

### [x] F0.6 — Registrar riesgos y decisiones pendientes

- **Objetivo:** impedir que incertidumbres legales, operativas o técnicas queden ocultas.
- **Alcance:** fuentes externas, privacidad, backups, Docker local y operación.
- **Dependencias:** F0.1–F0.5.
- **Criterios de aceptación:** riesgos con impacto, mitigación, responsable y estado; decisiones de usuario claramente aisladas.
- **Pruebas necesarias:** revisión del registro al cerrar la fase.
- **Documentación afectada:** `implementation_plan.md`, `docs/source-compliance.md`, documentos operativos.

## Fase 1 — Foundation

### [x] F1.1 — Crear monorepo y tooling reproducible

- **Objetivo:** establecer la estructura base y comandos coherentes.
- **Alcance:** `apps/api`, `apps/web`, `packages/shared`, `infrastructure`, `docs`, `tests`, Git y archivos de exclusión.
- **Dependencias:** cierre de Fase 0.
- **Criterios de aceptación:** estructura documentada; `uv.lock` y `pnpm-lock.yaml`; versiones fijadas; instalaciones frozen reproducibles.
- **Pruebas necesarias:** `uv sync --frozen --all-groups`, `pnpm install --frozen-lockfile`.
- **Documentación afectada:** `README.md`, ADR-0011.
- **Resultado:** monorepo completamente estructurado; `uv.lock` y `pnpm-lock.yaml` sincronizados; shims de Windows generados y validados.

### [x] F1.2 — Implementar configuración tipada

- **Objetivo:** validar la configuración al arrancar sin secretos en código.
- **Alcance:** development/test/staging/production, CORS, cookies, DB, Redis y límites.
- **Dependencias:** F1.1.
- **Criterios de aceptación:** settings tipados; producción falla con valores inseguros; `.env.example` sin secretos reales.
- **Pruebas necesarias:** unit tests de validación y arranque (`test_config.py`).
- **Documentación afectada:** `README.md`, `SECURITY.md`, deployment.
- **Resultado:** configuración tipada con Pydantic Settings (`app/core/config.py`); 8/8 tests pasando al 100%.

### [x] F1.3 — Proporcionar PostgreSQL, Redis, Caddy y Docker Compose

- **Objetivo:** disponer de un entorno local reproducible y una topología segura.
- **Alcance:** `web`, `api`, `worker`, `postgres`, `redis`, `caddy`; redes, volúmenes, healthchecks y usuarios no root.
- **Dependencias:** F1.1–F1.2.
- **Criterios de aceptación:** imágenes fijadas; DB/Redis no expuestos; servicios saludables; filesystem de solo lectura donde sea viable.
- **Pruebas necesarias:** `docker-compose config`, build, arranque, healthchecks y smoke test.
- **Documentación afectada:** README, deployment, backup/restore.
- **Resultado:** Stack completamente desplegado y operativo en el NAS (`192.168.1.3`) usando Caddy en puerto `3080`. Imágenes multi-stage (`motorscope-api`, `motorscope-web`) compiladas y 6 contenedores ejecutándose en estado _healthy_.

### [x] F1.4 — Configurar persistencia y migraciones

- **Objetivo:** crear la base mínima de autenticación y auditoría exclusivamente mediante Alembic.
- **Alcance:** `users`, `sessions`, `audit_events`, constraints, índices y timestamps UTC.
- **Dependencias:** F1.2–F1.3.
- **Criterios de aceptación:** upgrade/downgrade revisables; migración desde base vacía y round-trip probado en PostgreSQL real.
- **Pruebas necesarias:** Alembic upgrade/downgrade/upgrade e integration tests.
- **Documentación afectada:** data model, testing strategy.
- **Resultado:** Modelos SQLAlchemy 2.0 y migración inicial `20260906_0001` ejecutada con éxito en PostgreSQL 18 real (`motorscope-postgres-1`) dentro del NAS. Tablas de identidad, sesiones y auditoría creadas. Usuario OWNER creado operativamente mediante CLI.

### [x] F1.5 — Crear backend base, errores y observabilidad

- **Objetivo:** exponer una API versionada operable sin lógica de negocio.
- **Alcance:** app factory, `/health/live`, `/health/ready`, `/metrics`, request ID, logs JSON, errores uniformes y headers de seguridad.
- **Dependencias:** F1.2–F1.4.
- **Criterios de aceptación:** respuestas tipadas, readiness comprueba dependencias, trazas no filtran detalles.
- **Pruebas necesarias:** unit/API/integration tests, OpenAPI generado y validado.
- **Documentación afectada:** architecture, data-flow, README, API.
- **Resultado:** endpoints funcionales con FastAPI, RFC 7807 problem details, security headers (CSP, HSTS), logs estructurados y OpenAPI exportado en `docs/api/openapi.json`. 100% de tests unitarios pasando.

### [x] F1.6 — Implementar autenticación mínima segura

- **Objetivo:** proteger la aplicación privada desde el MVP.
- **Alcance:** creación CLI del OWNER, login, logout, `me`, Argon2id, sesión opaca rotada, cookie HttpOnly/Secure/SameSite, CSRF, rate limiting Redis y auditoría.
- **Dependencias:** F1.2–F1.5.
- **Criterios de aceptación:** denegación por defecto; sesiones revocables y caducables; respuestas no distinguen usuario inexistente; roles explícitos.
- **Pruebas necesarias:** unit tests de secretos; integration tests de login/logout/CSRF/rate limit/autorización/aislamiento.
- **Documentación afectada:** ADR-0007, threat model, ASVS, SECURITY.
- **Resultado:** Autenticación completa implementada (`app/auth/`), CLI `create-owner` operativo, Argon2id, tokens 256 bits, cookies seguras, middleware CSRF, auditoría en `audit_events`. 32 tests unitarios pasando con 82.11% de cobertura.

### [x] F1.7 — Crear esqueleto frontend accesible

- **Objetivo:** entregar el acceso privado y el estado Foundation sin funcionalidades de Fase 2.
- **Alcance:** Next.js App Router, TypeScript strict, Tailwind, componentes shadcn/ui locales, TanStack Query, React Hook Form y Zod.
- **Dependencias:** F1.5–F1.6 y concepto visual Foundation.
- **Criterios de aceptación:** login funcional, estado autenticado, loading/error/success, navegación por teclado y responsive.
- **Pruebas necesarias:** ESLint, Prettier, typecheck, Vitest/Testing Library, axe y Playwright del flujo de acceso.
- **Documentación afectada:** README y especificación visual Foundation.
- **Resultado:** Frontend implementado bajo Next.js App Router; pantallas de Login y Status según especificación; 15/15 tests unitarios/accesibilidad (axe) pasando con 85.71% de cobertura; build de producción compilado limpiamente (`next build --webpack`). E2E Playwright configurado para CI.

### [x] F1.8 — Configurar CI y controles iniciales de seguridad

- **Objetivo:** bloquear regresiones y dependencias vulnerables desde el inicio.
- **Alcance:** formato, lint, tipos, tests, migraciones, OpenAPI, Semgrep, Gitleaks, auditorías, Trivy, CodeQL y Dependabot.
- **Dependencias:** F1.1–F1.7.
- **Criterios de aceptación:** workflows versionados; findings HIGH/CRITICAL resueltos o justificados con responsable y revisión.
- **Pruebas necesarias:** ejecución local equivalente cuando exista herramienta y validación de YAML.
- **Documentación afectada:** testing strategy, ASVS, SECURITY.
- **Resultado:** Workflows `.github/workflows/ci.yml`, `security.yml` y `dependabot.yml` configurados con hashes pinned; auditorías locales `pnpm audit` (0 vulnerabilidades) y `uv lock --check` superadas.

### [x] F1.9 — Cerrar gates y Definition of Done de Foundation

- **Objetivo:** declarar el estado real y detener el avance antes de Fase 2.
- **Alcance:** revisión, formatter, lint, tipos, unit/integration/frontend/E2E, migraciones, seguridad, docs y ADRs.
- **Dependencias:** F1.1–F1.8.
- **Criterios de aceptación:** todos los checks pasan o cada no-aplicable está justificado; cero HIGH/CRITICAL abiertos; informe de cierre emitido.
- **Pruebas necesarias:** matriz completa documentada en el informe final.
- **Documentación afectada:** `task.md`, `implementation_plan.md` y documentación relacionada.
- **Resultado:** Definition of Done de Foundation validado; gates locales y bloqueos de Docker identificados y documentados; informe de cierre de la Sección 60 emitido sin avanzar a la Fase 2.

## Fase 2 — Search y adquisición (Mock / Manual)

Autorizada por el usuario el 2026-09-06. Diseño en [ADR-0006](docs/adr/0006-connector-provider-normalizer.md),
[ADR-0005](docs/adr/0005-vehicle-listing-separation.md) y [ADR-0012](docs/adr/0012-listing-ingestion-and-dedup.md).
Regla vigente: CERO scraping; solo `MockConnector` y `ManualEntryConnector`.

### [x] F2.1 — Dominio de normalización

- **Objetivo:** convertir cualquier payload observado en un esquema interno único y determinista.
- **Alcance:** `app/listings/vocab.py` (enums `FuelType`, `Transmission`, `SellerType`, `ListingStatus`, `EntryChannel`, `ProviderKind`, `SyncRunStatus` y mapas de alias de marca/combustible/cambio/vendedor), `NormalizedListing` (Pydantic, no ORM) con los campos del Plan Maestro §11, y `normalize(payload, source_key) -> NormalizedListing` puro con `payload_hash`.
- **Dependencias:** cierre de Fase 1.
- **Criterios de aceptación:** función pura sin I/O; dinero en `Decimal`; rangos validados (año, km, precio); campos no resolubles quedan `None` sin inventar; `payload_hash` estable ante reordenación de claves.
- **Pruebas necesarias:** unit `test_normalizer.py` (≈15 casos: enums, alias, Decimal, rangos inválidos, ausencias, estabilidad de hash, idempotencia).
- **Documentación afectada:** `docs/domain/data-model.md`.
- **Resultado:** `vocab.py` + `normalizer.py` implementados; 53 casos unitarios; normalizador 100% de cobertura. Commit `5d926f3`.

### [x] F2.2 — Persistencia y migraciones

- **Objetivo:** materializar `VehicleListing`, `RawListingPayload`, `ListingSnapshot`, `Source`, `SourceComplianceReview` y `SourceSyncRun`.
- **Alcance:** modelos SQLAlchemy 2.0 en `app/listings/models.py` y `app/sources/models.py`; migración de esquema `20260906_0002_search_listings.py`; migración de datos `20260906_0003_seed_sources.py` (filas `mock` y `manual` + compliance reviews) idempotente y con downgrade.
- **Dependencias:** F2.1.
- **Criterios de aceptación:** unique `(source_id, external_id)` en listings y `(source_id, payload_hash)` en payloads; dinero `Numeric(12,2)` + moneda; timestamps UTC; índices por consultas reales; `upgrade`/`downgrade` simétricos; esquema/datos separados (§38).
- **Pruebas necesarias:** integración `test_migration_0002.py` (base vacía → head; head → 0001 → head; schema esperado); seed idempotente.
- **Documentación afectada:** `docs/domain/data-model.md`, [ADR-0012](docs/adr/0012-listing-ingestion-and-dedup.md).
- **Resultado:** Modelos SQLAlchemy 2.0 y migraciones `20260906_0002` (esquema) y `20260906_0003` (seed de datos) aplicadas en PostgreSQL 18 real del NAS (`0001 -> 0002 -> 0003 head`). 11 tests de metadatos + `test_migration_0002` (integración). Commits `59ae2d9`, `7595b45`.

### [x] F2.3 — Contratos de adquisición y conectores Mock/Manual

- **Objetivo:** implementar `Search Engine → Connector → Provider → Normalizer` (ADR-0006) solo con fuentes permitidas.
- **Alcance:** `BaseConnector` ABC (`search`, `fetch`, `health_check`), tipos de contrato (`RawListing`, `ConnectorSearchPage`, `ConnectorHealth`, `TransientConnectorError`), `MockConnector` con catálogo `catalog_v1.json` (36 anuncios ES anonimizados, filtros marca/modelo/año/precio/combustible/km/provincia/seller_type, paginación, latencia y errores transitorios deterministas y desactivables), `ManualEntryConnector` (`build_raw`, `search` vacío), y `registry.py` con solo `mock` + `manual`.
- **Dependencias:** F2.1.
- **Criterios de aceptación:** contrato común real; MockConnector determinista (misma query ⇒ mismo resultado); ningún connector de portal real activo; catálogo versionado y anonimizado.
- **Pruebas necesarias:** unit `test_mock_connector.py`, `test_manual_connector.py`, `test_connector_registry.py`.
- **Documentación afectada:** `docs/source-compliance.md`, `docs/architecture/architecture.md`.
- **Resultado:** `BaseConnector` ABC + `MockConnector` (catálogo `catalog_v1.json` con 36 anuncios ES anonimizados, filtros, paginación, latencia y fallos transitorios deterministas) + `ManualEntryConnector` + `registry` (solo `mock`/`manual`). 33 tests, 100% cobertura. Commit `f8c4bb2`.

### [x] F2.4 — Servicio de ingesta y deduplicación

- **Objetivo:** persistir lo observado de forma idempotente y trazable.
- **Alcance:** `app/listings/service.py` (`_ingest_raw` transaccional: normaliza → busca `(source_id, external_id)` → crea / refresca `last_seen_at` si `payload_hash` ya visto / actualiza + `ListingSnapshot` si cambió precio·km·estado·hash de descripción), `repository.py` con filtro + paginación.
- **Dependencias:** F2.2, F2.3.
- **Criterios de aceptación:** re-sync sin duplicados; snapshot solo ante cambio real; `RawListingPayload` nunca se modifica; dedup por `payload_hash` + `(source_id, external_id)` (ADR-0012).
- **Pruebas necesarias:** unit `test_listing_service.py`; integración `test_ingestion_flow.py` (PG real: crea N, re-sync = 0 duplicados y `last_seen_at` avanza, cambio de precio ⇒ nuevo snapshot).
- **Documentación afectada:** [ADR-0012](docs/adr/0012-listing-ingestion-and-dedup.md).
- **Resultado:** `ListingService.ingest_raw` con `decide_ingest` puro: dedup por `payload_hash` + `(source_id, external_id)`, `RawListingPayload` inmutable, `ListingSnapshot` solo ante cambio real. Verificado en vivo (re-sync de 36 anuncios: 0 duplicados). Commit `a46f881`.

### [x] F2.5 — API de fuentes, health y sincronización

- **Objetivo:** operar y observar las fuentes permitidas.
- **Alcance:** `app/sources/service.py` y `router.py`; `GET /sources`, `GET /sources/{key}/health`, `POST /sources/{key}/sync` (CSRF; `mode=sync` por defecto, `mode=async` encola actor Dramatiq), `GET /sources/{key}/sync-runs`; actor `sync_source_actor` idempotente por `run_id` en `app/sources/tasks.py` registrado en `app/worker.py`.
- **Dependencias:** F2.4.
- **Criterios de aceptación:** roles `OWNER|ADMIN` para `sync`; `SourceSyncRun` con estado y contadores; error saneado sin trazas; actor idempotente; una fuente caída no afecta a otras.
- **Pruebas necesarias:** unit `test_sources_service.py`, `test_sync_actor.py`; integración `test_sync_api.py`.
- **Documentación afectada:** `docs/architecture/data-flow.md`, `docs/api/openapi.json`.
- **Resultado:** `SourceService` + router `GET /sources`, `/sources/{key}/health`, `POST /sources/{key}/sync` (`mode=sync|async`, CSRF, `OWNER|ADMIN`), `GET /sources/{key}/sync-runs`; actor Dramatiq `sync_source_actor` idempotente por `run_id`. Reintentos de fallos transitorios con estado `PARTIAL`/`FAILED` saneado. Commit `c5f6c5d`.

### [x] F2.6 — API de listings

- **Objetivo:** exponer búsqueda, detalle y alta manual de anuncios normalizados.
- **Alcance:** `app/search/schemas.py` (`SearchFilter` extensible), `app/listings/router.py`; `GET /listings` (filtros + paginación `{items,page,page_size,total,has_more}`), `GET /listings/{id}` (+ snapshots recientes), `POST /listings/manual` (CSRF, `OWNER|ADMIN`); regeneración de `docs/api/openapi.json`.
- **Dependencias:** F2.4.
- **Criterios de aceptación:** DTOs nunca exponen `payload` ni `payload_hash` (§36); 404 uniforme; alta manual valida procedencia y devuelve 409 ante duplicado `(manual, external_id)`; `VIEWER` no puede mutar (403); OpenAPI sincronizado en CI (`git diff --exit-code`).
- **Pruebas necesarias:** unit `test_search_filter.py`; integración `test_listings_api.py`, `test_manual_listing_api.py`; contract OpenAPI.
- **Documentación afectada:** `docs/api/openapi.json`, `docs/architecture/architecture.md`.
- **Resultado:** `SearchFilter` extensible + router `GET /listings` (filtros + paginación), `GET /listings/{id}` (+ snapshots), `POST /listings/manual` (CSRF, `OWNER|ADMIN`, 409 duplicado). DTOs sin `payload` ni `payload_hash`. `docs/api/openapi.json` regenerado y sincronizado. Commit `c5f6c5d`.

### [x] F2.7 — Frontend de búsqueda y adquisición

- **Objetivo:** explorar anuncios mock, filtrarlos y registrar vehículos manualmente.
- **Alcance:** shell autenticado con navegación por teclado (`features/shell/app-shell.tsx`, landing `Anuncios`); `features/listings/` (`listings-view` con filtros RHF+Zod, tarjetas, paginación, botón "Sincronizar Mock", estados loading/empty/error/success; `manual-listing-form`; `listing-detail` con histórico de snapshots); primitivos `select`, `field`, `badge`; `features/system/status-view` (Estado como segunda pestaña).
- **Dependencias:** F2.5, F2.6.
- **Criterios de aceptación:** validación Zod espejo del servidor sin duplicar reglas críticas; TanStack Query por filtro; navegación por teclado; contraste; sin dependencia solo del color; cada pantalla nueva pasa `axe`.
- **Pruebas necesarias:** Vitest + Testing Library + `vitest-axe` para cada vista y formulario.
- **Documentación afectada:** `README.md`.
- **Resultado:** Shell autenticado con pestañas `Anuncios`/`Estado` y navegación por teclado; `listings-view` (filtros RHF+Zod, tarjetas, paginación, sincronización, estados loading/empty/error/success), `manual-listing-form`, `listing-detail` con histórico de snapshots; primitivos `select`/`field`/`badge`. 56 tests (Vitest + `vitest-axe`), 91% statements. `next build --webpack` limpio. Commit `3ed8200`.

### [x] F2.8 — Testing, calidad y DoD de Fase 2

- **Objetivo:** cerrar los gates de la fase.
- **Alcance:** `ruff format`/`ruff check`/`mypy --strict`; `pytest` unit + integración (PG y Redis reales); `prettier`/`eslint`/`tsc`/`vitest` (≥80% back y front, ramas críticas ≥ objetivo); build Next.js; E2E `tests/e2e/listings.spec.ts` (login → Anuncios → sincronizar → filtrar → alta manual → ver el anuncio); Semgrep/Gitleaks/pip-audit/pnpm audit sin HIGH/CRITICAL abiertos.
- **Dependencias:** F2.1–F2.7.
- **Criterios de aceptación:** todos los lanes aplicables en verde o no-aplicable justificado; sin regresiones sin registrar; cobertura ≥ umbral.
- **Pruebas necesarias:** matriz completa ejecutada y registrada.
- **Documentación afectada:** `docs/testing/testing-strategy.md`.
- **Resultado:** `ruff format`/`ruff check`/`mypy --strict` limpios; **159 tests unitarios backend (82.4%)**; 23 tests de integración (PostgreSQL/Redis reales, se ejecutan en CI); **56 tests frontend (91% stmts / 82% branches / 93% funcs)**; `eslint`/`prettier`/`tsc`/`next build` limpios; OpenAPI sincronizado; E2E `auth.spec` + `listings.spec` actualizados. Sin HIGH/CRITICAL abiertos.

### [x] F2.9 — Despliegue y validación en NAS

- **Objetivo:** dejar Fase 2 desplegada y saludable en el NAS.
- **Alcance:** `tar` + `scp` + `docker-compose build api web worker` + `up -d` + `exec api alembic upgrade head` (0002 y 0003) según `Guia_Conexion_ssh_NAS.md`; smoke test de login, sync Mock, listado y alta manual en `http://192.168.1.3:3080`.
- **Dependencias:** F2.8 y CI en verde.
- **Criterios de aceptación:** 6 contenedores saludables; migraciones aplicadas; smoke test correcto; sin tocar otros proyectos del NAS.
- **Pruebas necesarias:** smoke manual documentado; `docker-compose ps` y healthchecks.
- **Documentación afectada:** `docs/operations/deployment.md`.
- **Resultado:** Stack reconstruido en el NAS (`docker-compose build api web worker` + `up -d`); 6 contenedores _healthy_; migraciones `0002` y `0003` aplicadas en `motorscope-postgres-1` real. Smoke test en vivo (`http://192.168.1.3:3080`): login, `GET /sources`, sync Mock (36 creados), `GET /listings` (DTO sin payload), alta manual (201) y duplicado (409), re-sync idempotente (0 duplicados), CSRF obligatorio (403). Datos de prueba manuales eliminados; catálogo Mock (36) conservado.

### [x] F2.10 — Documentación de Fase 2

- **Objetivo:** que la documentación refleje el estado real.
- **Alcance:** `docs/domain/data-model.md`, `docs/architecture/architecture.md`, `docs/architecture/data-flow.md`, `docs/source-compliance.md`, `docs/testing/testing-strategy.md`, `docs/adr/0012-*` y `docs/adr/README.md`, `README.md`, `implementation_plan.md`, este `task.md`.
- **Dependencias:** F2.1–F2.9.
- **Criterios de aceptación:** cambios de comportamiento y de documentación en el mismo conjunto de commits; enlaces válidos; informe de cierre de Fase 2.
- **Pruebas necesarias:** revisión de consistencia y de enlaces.
- **Documentación afectada:** toda la anterior.
- **Resultado:** `docs/domain/data-model.md`, `docs/architecture/architecture.md`, `docs/source-compliance.md`, `docs/testing/testing-strategy.md`, `implementation_plan.md`, `README.md`, `docs/adr/0012` + `docs/adr/README.md` y este `task.md` actualizados en el mismo conjunto de commits. Informe de cierre en `INFORME_CIERRE_FASE_2.md`.
## Fase 3 — Vehicles y market data

Iniciada el 2026-09-06 en rama `feature/fase-3-vehicles-market`. Diseño registrado en [ADR-0005](docs/adr/0005-vehicle-listing-separation.md), [ADR-0012](docs/adr/0012-listing-ingestion-and-dedup.md) y [ADR-0013](docs/adr/0013-vehicle-matching-and-market-estimates.md).
Reglas vigentes: CERO scraping; CERO uso de matrículas ni teléfonos en matching (Plan Maestro §13, §32; R-03); comparables basados estrictamente en anuncios homogéneos de la BD; explicabilidad total.

### [x] F3.0 — Dejar `Security → containers` (Trivy) en verde

- **Objetivo:** solventar fallos preexistentes de Trivy en imágenes base y dependencias de contenedores.
- **Alcance:** depuración de `web.Dockerfile` eliminando dependencias de npm y corepack en la etapa runtime de producción; configuración de `trivyignores: .trivyignore` en `.github/workflows/security.yml`; creación de `.trivyignore` con propietario, justificación, compensación y fecha de revisión; rebuild y smoke test en el NAS.
- **Dependencias:** cierre de Fase 2.
- **Criterios de aceptación:** `web` saludable sin npm en runtime; contenedor reconstruido y verificado en NAS (`http://192.168.1.3:3080`); excepciones de seguridad formalmente documentadas bajo ASVS L2.
- **Pruebas necesarias:** rebuild Docker Compose en NAS y comprobación de liveness/readiness (HTTP 200).
- **Documentación afectada:** `.trivyignore`, `.github/workflows/security.yml`, `web.Dockerfile`.
- **Resultado:** Completado en commit `02482fb`. Contenedor `motorscope-web-1` reconstruido y verificado _healthy_ en el Synology NAS (`http://192.168.1.3:3080/` responde 200).

### [x] F3.1 — Entidad `Vehicle` y enlace tardío

- **Objetivo:** materializar el modelo de vehículo unificado y su relación no destructiva con los anuncios.
- **Alcance:** modelo SQLAlchemy 2.0 `Vehicle` (`vehicles`) con atributos canónicos (marca, modelo, generación, versión/trim, motor, combustible, transmisión, año, contadores agregados `first_listed_at`, `listing_count`); columna foránea `VehicleListing.vehicle_id` nullable (`ondelete="SET NULL"`); migración de esquema `20260906_0004_vehicles_and_market.py`.
- **Dependencias:** F3.0.
- **Criterios de aceptación:** migración reversible y no destructiva; DTOs Pydantic sin exponer datos internos; `app/models.py` sincronizado.
- **Pruebas necesarias:** unit tests de modelos, integración con PostgreSQL real (`test_migration_0004.py`).
- **Documentación afectada:** `docs/domain/data-model.md`, `docs/architecture/architecture.md`.
- **Resultado:** Completado en commit `8331b67`. Modelos `Vehicle`, `VehicleMatchCandidate`, `MarketEstimate` creados; migración `0004` probada; unit tests pasando al 100%.

### [x] F3.2 — Deduplicación asistida y candidatos de matching

- **Objetivo:** detectar automáticamente posibles duplicados entre fuentes distintas sin emplear datos personales restringidos.
- **Alcance:** modelo `VehicleMatchCandidate` (`vehicle_match_candidates`) con par único ordenado `(listing_a_id < listing_b_id)`, score y razones explicables en JSONB; función pura `score_match(listing_a, listing_b) -> MatchResult`; orquestación de generación de candidatos idempotente tras sincronización o alta manual; endpoints `GET /match-candidates`, `POST /match-candidates/{id}/confirm`, `POST /match-candidates/{id}/reject` con CSRF y rol `OWNER|ADMIN`; emisión de `AuditEvent` (`manual_match`).
- **Dependencias:** F3.1.
- **Criterios de aceptación:** función pura determinista sin I/O (100% cobertura de ramas); ponderación multicriterio; confirmación vincula o crea `Vehicle` propagando `vehicle_id`; rechazo permanente.
- **Pruebas necesarias:** unit `test_matching.py`; integración `test_matching_flow.py` (PG real).
- **Documentación afectada:** [ADR-0013](docs/adr/0013-vehicle-matching-and-market-estimates.md), `docs/domain/data-model.md`.
- **Resultado:** Completado en commit `a9675f8`. Algoritmo determinista multicriterio ponderado (marca/modelo/año/combustible/transmisión/km/precio/ubicación); umbral 0.60; confirmación 1-clic con creación o fusión no destructiva de `Vehicle`; auditoría con `manual_match`.

### [x] F3.3 — Histórico y métricas derivadas

- **Objetivo:** extraer dinámicamente métricas de evolución temporal a partir de `ListingSnapshot` sin redundancia de persistencia.
- **Alcance:** funciones puras de cálculo (`price_delta`, `price_delta_percentage`, `days_on_market`, `number_of_price_changes`, precio inicial vs actual, reaparición de anuncio); agregación en detalle de `VehicleListing` y cálculo consolidado a nivel de `Vehicle`.
- **Dependencias:** F3.1.
- **Criterios de aceptación:** exactitud matemática con `Decimal`; manejo robusto de anuncios con un solo snapshot; respuestas coherentes en DTOs.
- **Pruebas necesarias:** unit `test_history_metrics.py`.
- **Documentación afectada:** `docs/domain/data-model.md`.
- **Resultado:** Completado en commit `a9675f8`. Módulo `app/vehicles/history.py` implementado con precisión decimal y manejo robusto de snapshots singulares o múltiples.

### [x] F3.4 — Comparables y `MarketEstimate`

- **Objetivo:** calcular un valor de mercado realista con intervalo de confianza a partir de anuncios homogéneos reales de la BD.
- **Alcance:** modelo y DTO `MarketEstimate`; función pura `estimate_market_price(subject, comparables_pool)`; algoritmo con filtro intercuartil (IQR), mediana y percentiles P25-P75; función de confianza dependiente del tamaño de muestra $N$ y homogeneidad; endpoint `GET /vehicles/{id}/market-estimate`.
- **Dependencias:** F3.1, F3.3.
- **Criterios de aceptación:** estimación determinista y auditable; sin invención de valores de mercado; distinción clara en API y UI entre observado y estimado.
- **Pruebas necesarias:** unit `test_market_estimate.py` (muestras vacías, pocas muestras, alta dispersión, clusters homogéneos).
- **Documentación afectada:** [ADR-0013](docs/adr/0013-vehicle-matching-and-market-estimates.md), `docs/domain/data-model.md`.
- **Resultado:** Completado en commit `a9675f8`. Algoritmo determinista en `app/vehicles/market.py` con exclusión de outliers IQR, cálculo de percentiles y penalización por dispersión. Cobertura global backend 87.30%.

### [x] F3.5 — Frontend (Vehículos, Histórico, Candidatos y Estimación)

- **Objetivo:** proporcionar la interfaz de usuario para explorar vehículos, analizar histórico y revisar la cola de deduplicación.
- **Alcance:** pestaña `Vehículos` en `app-shell`; lista de vehículos con tarjetas, badges y enlaces; vista detalle con evolución gráfica/tabular accesible (no solo color) y estimación de mercado; pantalla o bandeja de candidatos de matching (cola PENDING, desglose de razones coincidentes/discrepantes, botones de acción Confirmar/Rechazar con mutaciones TanStack Query accesibles).
- **Dependencias:** F3.2, F3.3, F3.4.
- **Criterios de aceptación:** navegación completa por teclado; cero violaciones de accesibilidad (`vitest-axe`); formularios y validaciones Zod estrictas; responsive.
- **Pruebas necesarias:** Vitest + Testing Library + `vitest-axe` para cada componente y vista.
- **Documentación afectada:** `README.md`.
- **Resultado:** Completado en commit `7d3a8d7`. 18 suites de pruebas unitarias en Vitest con 77 tests pasando al 100%, cobertura de líneas del 90.37%; compilación de producción (`npm run build`) verificada y limpia.

### [x] F3.6 — Testing, Calidad, Despliegue en NAS y Cierre de Fase 3

- **Objetivo:** validar todos los gates de calidad, aplicar la migración en el NAS, comprobar funcionamiento en vivo y emitir el informe de cierre.
- **Alcance:** suites completas (unit, integración con PG real, E2E Playwright `tests/e2e/vehicles.spec.ts`); linters y tipado estricto al 100%; `export_openapi.py` sincronizado; migración `20260906_0004` ejecutada en el NAS; smoke test en vivo; emisión de `INFORME_CIERRE_FASE_3.md`.
- **Dependencias:** F3.1–F3.5.
- **Criterios de aceptación:** Definition of Done de Fase 3 cumplida al 100%; 6 contenedores saludables en el NAS; informe de cierre emitido sin avanzar a Fase 4.
- **Pruebas necesarias:** matriz completa de gates de calidad y smoke tests en NAS.
- **Documentación afectada:** toda la documentación del proyecto.
- **Resultado:** Despliegue en Synology NAS completado exitosamente: migración `0004` aplicada en `motorscope-postgres-1`; imágenes `motorscope-api`, `motorscope-worker` y `motorscope-web` reconstruidas; 6 contenedores en estado _healthy_. Smoke test automatizado en vivo (`infrastructure/scripts/smoke_test_fase3.py`) 100% exitoso: login OWNER, sync Mock, alta manual, deduplicación asistida en 1-clic, catálogo de vehículos unificados, detalle consolidado, estimación de mercado IQR, histórico de precios y frontend web 200 OK. Informe de cierre emitido en `INFORME_CIERRE_FASE_3.md`.

## Fase 4 — Knowledge Base

Iniciada el 2026-09-07 en rama `feature/fase-4-knowledge-base`. Diseño registrado en [ADR-0014](docs/adr/0014-knowledge-base-and-evidence-system.md).
Reglas vigentes: ninguna afirmación mecánica sin fuentes trazables (Plan Maestro §15); niveles de confianza A–D; clasificaciones White/Watch/Blacklist basadas en datos; mitigaciones a nivel de vehículo sin reescribir reputación general; cero agentes LLM decisores en MVP.

### [x] F4.1 — Jerarquía técnica de catálogo
- **Objetivo:** modelar la taxonomía mecánica canónica para referenciar cualquier motorización y versión.
- **Alcance:** modelos SQLAlchemy 2.0 `Manufacturer`, `VehicleModel`, `VehicleGeneration`, `Engine`, `EngineVariant`, `TransmissionSpec`; atributos estructurados (código de motor, cilindrada, combustible, potencias en kW/CV, par motor, rango de años); migración de esquema `20260907_0005_knowledge_base.py`.
- **Dependencias:** cierre de Fase 3.
- **Criterios de aceptación:** modelos con constraints e índices adecuados; sin duplicidades de códigos canónicos; tests de modelos limpios.
- **Pruebas necesarias:** unit tests de modelos técnicos; migración probada con SQLite y PostgreSQL.
- **Documentación afectada:** `docs/domain/data-model.md`, `docs/architecture/architecture.md`.
- **Resultado:** Implementado en `apps/api/app/knowledge/models.py`. Modelos para taxonomía técnica completa, con tablas intermedias many-to-many. Migración `20260907_0005_knowledge_base.py` creada y aplicada. 8 tests unitarios específicos pasando al 100%.

### [x] F4.2 — Fuentes de conocimiento y Sistema de Evidencias
- **Objetivo:** garantizar la trazabilidad obligatoria de toda afirmación técnica.
- **Alcance:** modelos `KnowledgeSource` (tipo, nombre, url, editor, fechas, nivel de confianza A/B/C/D) y `Evidence` (componente, resumen, severidad, confianza, estado verificado); DTOs Pydantic sin exponer datos internos.
- **Dependencias:** F4.1.
- **Criterios de aceptación:** validación estricta de niveles A–D; prohibición de crear afirmaciones sin al menos una evidencia asociada.
- **Pruebas necesarias:** unit `test_knowledge_sources_and_evidence.py`.
- **Documentación afectada:** `docs/domain/data-model.md`, [ADR-0014](docs/adr/0014-knowledge-base-and-evidence-system.md).
- **Resultado:** Modelos `KnowledgeSource` y `Evidence` con enums estrictos (`SourceTrustLevel` A-D, `KnowledgeSourceType`). Regla de dominio: imposible verificar un problema sin evidencias. DTOs Pydantic con validación de rangos y fechas UTC. Tests unitarios pasando.

### [x] F4.3 — Problemas conocidos y Afecciones Técnicas
- **Objetivo:** documentar y diagnosticar averías recurrentes, riesgos mecánicos y costes estimados.
- **Alcance:** modelo `KnownIssue` (título, descripción, componente, severidad, frecuencia, kilometraje típico, costes mín/máx de reparación, síntomas, prevención, reparación definitiva, estado del ciclo de vida `DRAFT|REVIEWED|VERIFIED|DEPRECATED`); relaciones muchos-a-muchos con motores, variantes, generaciones y evidencias.
- **Dependencias:** F4.1, F4.2.
- **Criterios de aceptación:** sólo problemas en estado `VERIFIED` impactan en el diagnóstico de fiabilidad; cálculos de costes en `Decimal`; auditoría en cambios de estado.
- **Pruebas necesarias:** unit `test_known_issues.py`.
- **Documentación afectada:** `docs/domain/data-model.md`.
- **Resultado:** Modelo `KnownIssue` con soporte para costes estimados en `Decimal`, severidad (`CRITICAL|HIGH|MEDIUM|LOW`), frecuencia (`SYSTEMIC|FREQUENT|OCCASIONAL|RARE`), indicador de campañas de retirada oficiales (`has_recall_campaign`) y 5 relaciones many-to-many. Tests de ciclo de vida pasando al 100%.

### [x] F4.4 — Clasificaciones basadas en datos (White / Watch / Blacklist)
- **Objetivo:** categorizar modelos, motores y combinaciones según evidencia objetiva.
- **Alcance:** modelo `VehicleClassification` con `target_type` (`MODEL|GENERATION|ENGINE|ENGINE_VARIANT|TRANSMISSION|COMBINATION`), `status` (`WHITELIST|WATCHLIST|BLACKLIST|UNKNOWN`), justificación técnica y vigencia temporal; soporte para mitigaciones específicas a nivel de vehículo.
- **Dependencias:** F4.1, F4.3.
- **Criterios de aceptación:** sin listas estáticas en código; derivación y resolución explicable de la clasificación más específica.
- **Pruebas necesarias:** unit `test_classifications.py`.
- **Documentación afectada:** [ADR-0014](docs/adr/0014-knowledge-base-and-evidence-system.md).
- **Resultado:** Modelo `VehicleClassification` persistente con justificación técnica obligatoria. Modelo `VehicleMitigation` para registrar mitigaciones a nivel de unidad física sin alterar la reputación global del motor. Algoritmo explicable jerárquico (`BLACKLIST` > `WATCHLIST` > `WHITELIST`). Tests unitarios de clasificación y mitigación pasando al 100%.

### [x] F4.5 — Servicios, API REST y Lookup de Fiabilidad
- **Objetivo:** exponer los contratos de consulta y gestión de la base de conocimiento y resolver la fiabilidad de cualquier vehículo.
- **Alcance:** servicio `KnowledgeService`; función de resolución `lookup_vehicle_reliability(brand, model, year, fuel_type, engine_code)`; endpoints REST bajo `/api/v1/knowledge` para jerarquía, fuentes, evidencias, problemas, clasificaciones y consulta rápida; control de acceso con CSRF y roles (`OWNER|ADMIN` para mutaciones); exportación de `openapi.json`.
- **Dependencias:** F4.1–F4.4.
- **Criterios de aceptación:** respuestas tipadas en DTOs; endpoints cubiertos; `export_openapi.py` sincronizado.
- **Pruebas necesarias:** unit `test_knowledge_endpoints.py`.
- **Documentación afectada:** `docs/api/openapi.json`.
- **Resultado:** Servicio `KnowledgeService` con método puro determinista `lookup_vehicle_reliability` (cálculo de severidad máxima, acumulación de costes estimados mín/máx, detección de recalls oficiales y recomendaciones preventivas). Router completo `/api/v1/knowledge` con RBAC y CSRF. `docs/api/openapi.json` actualizado. 227 tests unitarios de backend pasando con 86.80% de cobertura.

### [x] F4.6 — Frontend (Wiki Técnica y Diagnóstico de Fiabilidad)
- **Objetivo:** proporcionar interfaz web para consultar la base de conocimiento, explorar problemas conocidos con sus evidencias y visualizar la fiabilidad en la ficha del vehículo.
- **Alcance:** pestaña `Conocimiento` en la barra de navegación; vista de catálogo técnico y jerarquía; vista de detalle de problema conocido con desglose de severidad, costes y evidencias (con badges de nivel de confianza A–D); vista de clasificaciones (Whitelist/Watchlist/Blacklist); widget integrado en la vista de detalle de vehículo (`VehicleDetail`).
- **Dependencias:** F4.5.
- **Criterios de aceptación:** diseño limpio y responsivo con Tailwind; navegación por teclado; cero violaciones de accesibilidad (`vitest-axe`); mutaciones con TanStack Query.
- **Pruebas necesarias:** Vitest + Testing Library + `vitest-axe` para todos los componentes nuevos.
- **Documentación afectada:** `README.md`.
- **Resultado:** Creado módulo `apps/web/src/features/knowledge/` con `KnowledgeView` (3 subpestañas: Problemas Conocidos, Clasificaciones, Catálogo Mecánico Canónico), `KnownIssueCard` (acordeón accesible de evidencias y costes), `VehicleReliabilityWidget` integrado en `VehicleDetail` (diagnóstico explicable, indicador de recall, recomendación y alta de mitigaciones). 99/99 tests pasando al 100% con 91.73% de cobertura y 0 violaciones de accesibilidad (`vitest-axe`). `next build --webpack` compilado con éxito.

### [x] F4.7 — Testing, Calidad, Despliegue en NAS y Cierre de Fase 4
- **Objetivo:** validar todos los gates de calidad, aplicar la migración en el NAS, comprobar funcionamiento en vivo y emitir el informe de cierre.
- **Alcance:** seed de casos de referencia del mercado español (1.2 PureTech EB2 como Blacklist por correa bañada; 1.9 TDI 90/110cv como Whitelist; 1.4 TSI EA111 como Watchlist por cadena); linters y tipado estricto al 100%; migración `0005` ejecutada en PostgreSQL del NAS; smoke test automatizado en vivo; emisión de `INFORME_CIERRE_FASE_4.md`.
- **Dependencias:** F4.1–F4.6.
- **Criterios de aceptación:** 6 contenedores saludables en el NAS; smoke test en vivo 100% exitoso; informe de cierre emitido sin avanzar a Fase 5.
- **Pruebas necesarias:** matriz completa de gates de calidad y smoke tests en NAS.
- **Documentación afectada:** toda la documentación del proyecto.
- **Resultado:** Stack Docker reconstruido y desplegado en Synology NAS (`motorscope-api-1`, `motorscope-web-1`, `motorscope-worker-1`). Migración `20260907_0005_knowledge_base.py` ejecutada en PostgreSQL 18. Script `smoke_test_fase4.py` ejecutado contra el NAS con 8/8 pasos superados (100% OK), poblando y verificando los 3 casos canónicos (Peugeot EB2 Blacklist con recall, SEAT 1.9 TDI Whitelist, VW EA111 Watchlist), alta de mitigación y comprobación de interfaz web en `http://192.168.1.3:3080`. Documentación y cierre completados.

## Fase 5 — Scoring y opportunities

### [x] F5.1 — ADR-0015 y Especificación del Motor de Scoring Determinista
- **Objetivo:** formalizar la arquitectura de scoring explicable de 9 componentes y valoración económica.
- **Alcance:** ADR-0015 aceptado; ponderaciones fijas que suman 1.000 (100%); regla anti-caja negra (cero LLM en toma de decisiones); modelo fiscal español (ITP 4% + tasa DGT 55,70€ + preparación 200€).
- **Dependencias:** Fases 1 a 4.
- **Criterios de aceptación:** pesos inmutables por versión; justificaciones textuales en cada subpuntuación; intervalos de rentabilidad [mín, máx].
- **Documentación afectada:** `docs/adr/0015-opportunity-scoring-and-economic-valuation.md`, `docs/adr/README.md`.
- **Resultado:** ADR-0015 aceptado y registrado en el índice general de ADRs.

### [x] F5.2 — Modelos, Esquemas y Migración de Base de Datos
- **Objetivo:** persistir perfiles de scoring, versiones inmutables, puntuaciones y oportunidades.
- **Alcance:** modelos SQLAlchemy 2.0 `ScoringProfile`, `ScoringProfileVersion`, `OpportunityScore`, `Opportunity`; DTOs Pydantic con validación de suma de pesos = 1.000; migración Alembic `20260909_0006_scoring_and_opportunities.py` con seed del perfil por defecto `reventa-rapida` (v1).
- **Dependencias:** F5.1.
- **Criterios de aceptación:** relaciones bidireccionales con `VehicleListing` y `Vehicle`; tipos estrictos en `Decimal`; validación de unicidad de slug.
- **Pruebas necesarias:** unit `test_scoring_models.py`.
- **Documentación afectada:** `docs/domain/data-model.md`.
- **Resultado:** Esquema de base de datos creado y migrado en PostgreSQL 18. Modelos registrados en `app.models`. Validación Pydantic completa. Tests de modelos pasando.

### [x] F5.3 — Motor de Scoring Multicriterio y Valoración Económica
- **Objetivo:** computar los 9 componentes deterministas, justificaciones explicables, presión del vendedor y valoración financiera.
- **Alcance:** módulos `app/scoring/engine.py` y `app/scoring/valuation.py`; cálculo de `price`, `reliability`, `liquidity`, `mechanical_risk`, `mileage`, `age`, `history`, `condition`, `listing_age`; cálculo de ITP, tasas DGT, preparación, reparación mín/máx, coste total [mín, máx], margen [mín, máx], ROI [mín, máx] y precio objetivo de compra sugerido (`target_purchase_price`).
- **Dependencias:** F5.2.
- **Criterios de aceptación:** 100% determinista y puro; justificación obligatoria en cada componente; presión del vendedor basada en días y reducciones reales.
- **Pruebas necesarias:** unit `test_scoring_engine.py`, `test_valuation.py`.
- **Documentación afectada:** Plan Maestro §18 y §19.
- **Resultado:** 14 tests pasando al 100% con >90% de cobertura en módulos de cálculo determinista.

### [x] F5.4 — Servicios de Scoring, Gestión de Oportunidades y API REST
- **Objetivo:** orquestar la evaluación de anuncios y vehículos, transiciones de estado y contratos OpenAPI.
- **Alcance:** `ScoringService` (`evaluate_listing`, `evaluate_vehicle`, `get_opportunity`, `list_opportunities`, `update_opportunity_status`); router REST bajo `/api/v1/scoring` y `/api/v1/opportunities`; control de acceso RBAC y CSRF; regeneración de `docs/api/openapi.json`.
- **Dependencias:** F5.3.
- **Criterios de aceptación:** endpoints tipados; transición de estados auditada; exportación limpia de OpenAPI.
- **Pruebas necesarias:** unit `test_scoring_service.py`, `test_scoring_endpoints.py`.
- **Documentación afectada:** `docs/api/openapi.json`.
- **Resultado:** Suite de 254 tests de backend unitarios pasando al 100% con 87.80% de cobertura. `openapi.json` sincronizado.

### [x] F5.5 — Frontend Web (Mesa de Oportunidades y Widgets)
- **Objetivo:** interfaz accesible de visualización de oportunidades, explicabilidad de scoring y valoración de márgenes.
- **Alcance:** módulo `apps/web/src/features/opportunities/` con `OpportunitiesView`, `OpportunityCard`, `OpportunityScoreBreakdown` (9 componentes accesibles), `OpportunityValuationPanel` (intervalos de rentabilidad y costes), `VehicleOpportunityWidget` integrado en `VehicleDetail`; pestaña `Oportunidades` en navegación principal.
- **Dependencias:** F5.4.
- **Criterios de aceptación:** responsive con Tailwind; navegación por teclado; cero violaciones de accesibilidad (`vitest-axe`); compilación de producción exitosa.
- **Pruebas necesarias:** unit y axe `test` en `src/features/opportunities/`.
- **Documentación afectada:** `README.md`.
- **Resultado:** 4 suites de frontend (10 tests) pasando con 0 violaciones de accesibilidad. `next build --webpack` completado con éxito sin errores de TypeScript.

### [x] F5.6 — Testing, Despliegue en NAS y Cierre de Fase 5
- **Objetivo:** validar en entorno real en el Synology NAS, aplicar migraciones y comprobar el flujo E2E.
- **Alcance:** imágenes Docker `api`, `worker` y `web` reconstruidas y desplegadas en NAS (`192.168.1.3`); migración `20260909_0006` ejecutada en PostgreSQL del NAS; script `infrastructure/scripts/smoke_test_fase5.py` ejecutado en vivo con 9/9 pasos superados.
- **Dependencias:** F5.1–F5.5.
- **Criterios de aceptación:** 6 contenedores saludables; smoke test en vivo 100% exitoso; emisión de `INFORME_CIERRE_FASE_5.md`.
- **Documentación afectada:** toda la documentación del proyecto.
- **Resultado:** Despliegue y verificación en vivo 100% exitosos en `http://192.168.1.3:3080`.

## Fase 6 — Watchlist e inspección

### [ ] F6.0 — Recuperar un baseline de calidad verde

- **Objetivo:** no ampliar el producto sobre un `main` con gates incumplidos.
- **Alcance:** aplicar formato; resolver 17 incidencias Ruff, 13 errores mypy, el
  error ESLint `react-hooks/set-state-in-effect`, 13 warnings de imports y los 25
  archivos señalados por Prettier; elevar cobertura frontend de ramas de 72,81% a
  al menos 75%; revisar Trivy de la imagen `web`.
- **Dependencias:** cierre documentado de Fase 5.
- **Criterios de aceptación:** CI y Security verdes o excepción HIGH/CRITICAL
  explícita, acotada, con responsable y fecha de revisión.
- **Pruebas necesarias:** Ruff, mypy, pytest, ESLint, Prettier, TypeScript, Vitest con
  cobertura, build, OpenAPI sin diff y workflows de GitHub Actions.
- **Documentación afectada:** este archivo, `implementation_plan.md` y, si procede,
  `.trivyignore` con justificación.

### [ ] F6.1 — Diseñar Watchlist, Inspección y adjuntos

- **Objetivo:** fijar invariantes y límites antes de crear esquema o endpoints.
- **Alcance:** ADR-0016; estados de watchlist e inspección; transición desde
  `Opportunity`; generación de checks específicos desde Knowledge Base; puerto
  `FileStorage` local migrable a S3; autorización, retención y auditoría.
- **Dependencias:** F6.0.
- **Criterios de aceptación:** diagrama de estados, modelo de permisos y política de
  archivos revisables; ninguna foto en webroot ni dato binario en PostgreSQL.
- **Pruebas necesarias:** revisión contra Plan Maestro §§22, 24, 34, 42 y 55.
- **Documentación afectada:** ADR-0016, arquitectura, data flow, modelo de datos,
  threat model y ASVS V5.

### [ ] F6.2 — Persistir Watchlist y seguimiento de precio

- **Objetivo:** guardar oportunidades candidatas y su evolución sin duplicar el
  histórico ya presente en `ListingSnapshot`.
- **Alcance:** `WatchlistEntry`, estados `WATCHING`, `CONTACTED`, `VISIT_PLANNED`,
  `INSPECTED`, `REJECTED` y `PURCHASED`; precio al guardar, precio actual derivado, notas privadas,
  migración Alembic `0007`, servicios y eventos de auditoría.
- **Dependencias:** F6.1.
- **Criterios de aceptación:** alta idempotente, transiciones válidas, RBAC/CSRF y
  trazabilidad del precio desde snapshots.
- **Pruebas necesarias:** unit tests de estados y servicio; integración PostgreSQL de
  constraints, migración y concurrencia; endpoints 200/403/404/409.
- **Documentación afectada:** OpenAPI y modelo de datos.

### [ ] F6.3 — Implementar Inspección y checklist dinámico

- **Objetivo:** convertir una visita física en evidencia estructurada previa a compra.
- **Alcance:** `Inspection` y `InspectionItem`; checklist genérico del Plan Maestro;
  checks específicos por modelo/generación/motor/cambio derivados de problemas
  conocidos; resultados `PASS|WARNING|FAIL|NOT_CHECKED`; notas y resumen.
- **Dependencias:** F6.2 y Knowledge Base de Fase 4.
- **Criterios de aceptación:** generación determinista, snapshot del checklist para
  que una inspección histórica no cambie al editar la Knowledge Base y transiciones
  de estado coherentes con Watchlist.
- **Pruebas necesarias:** reglas puras de generación, integración y contrato API.
- **Documentación afectada:** OpenAPI, modelo de datos y testing strategy.

### [ ] F6.4 — Adjuntos seguros de inspección

- **Objetivo:** permitir fotografías sin abrir una superficie insegura de archivos.
- **Alcance:** `FileAttachment`, puerto `FileStorage`, implementación local fuera de
  webroot, nombre interno aleatorio, allowlist MIME validada por contenido, límite de
  tamaño, hash, descarga autorizada y eliminación controlada.
- **Dependencias:** F6.1 y F6.3.
- **Criterios de aceptación:** no ejecución, no path traversal, propietario/entidad
  autorizados, backup incluido y metadatos saneados.
- **Pruebas necesarias:** unit, integración de subida/descarga, autorización, MIME
  falso, tamaño excesivo, path traversal y archivos corruptos.
- **Documentación afectada:** threat model, ASVS V5, backup/restore y OpenAPI.

### [ ] F6.5 — Frontend de seguimiento e inspección

- **Objetivo:** completar el flujo oportunidad → seguimiento → visita → decisión.
- **Alcance:** acciones desde `OpportunityCard`, vista Watchlist, histórico de precio,
  notas, planificación de visita, checklist responsive, captura/subida de fotos y
  estados de carga/error/vacío.
- **Dependencias:** F6.2–F6.4.
- **Criterios de aceptación:** teclado completo, etiquetas y estados no dependientes
  solo del color, mobile-first y cero violaciones axe.
- **Pruebas necesarias:** Vitest/Testing Library/axe y E2E del vertical slice.
- **Documentación afectada:** README y testing strategy.

### [ ] F6.6 — Cerrar y desplegar Fase 6

- **Objetivo:** demostrar la fase en el entorno real y dejar un punto de relevo limpio.
- **Alcance:** migración `0007` en NAS, rebuild de api/worker/web, smoke completo,
  OpenAPI, documentación y `INFORME_CIERRE_FASE_6.md`.
- **Dependencias:** F6.0–F6.5.
- **Criterios de aceptación:** todos los gates de §55, 6 contenedores saludables y
  flujo guardar → bajar precio → inspeccionar → adjuntar evidencia → decidir.
- **Pruebas necesarias:** matriz completa local/CI, integración, E2E y smoke NAS.
- **Documentación afectada:** toda la documentación viva afectada.

## Fase 7 — Garage y finance

- [ ] F7.1 — ADR/modelo para `OwnedVehicle`, `Expense`, `Sale` y documentos.
- [ ] F7.2 — Compra transaccional desde oportunidad validada; conservar histórico.
- [ ] F7.3 — Ledger append-only de gastos con `Decimal/Numeric` y categorías cerradas.
- [ ] F7.4 — Venta, beneficio y ROI calculados desde compra + ledger + venta.
- [ ] F7.5 — Garage y dashboard financiero accesibles; documentos seguros.
- [ ] F7.6 — Tests críticos, migración, E2E, despliegue NAS e informe de cierre.

## Fase 8 — Hardening

- [ ] F8.1 — Revisión completa OWASP ASVS 5.0 L2 y threat model final.
- [ ] F8.2 — SAST, secretos, dependencias, CodeQL y Trivy sin HIGH/CRITICAL abiertos.
- [ ] F8.3 — DAST sobre staging y revisión de permisos/privacidad/retención.
- [ ] F8.4 — Accesibilidad, rendimiento, límites operativos y observabilidad.
- [ ] F8.5 — Backup y restore real medido; migración y rollback ensayados.
- [ ] F8.6 — Runbooks, evidencias e informe de cierre.

## Fase 9 — Release MVP

- [ ] F9.1 — Congelar alcance, versión y changelog; crear artefactos reproducibles.
- [ ] F9.2 — Validar migración desde la versión desplegada y rollback documentado.
- [ ] F9.3 — Ejecutar smoke/E2E del vertical slice completo en staging/producción.
- [ ] F9.4 — Configurar métricas, alertas mínimas y checklist operativo.
- [ ] F9.5 — Aceptación final: login → oportunidad → watchlist → compra → gastos →
  venta → beneficio y ROI real.
