# Estado operativo del proyecto

Fuente operativa de verdad. Última actualización: 2026-09-06.

Estados: `[ ]` pendiente · `[~]` en progreso · `[x]` completado · `[!]` bloqueado.

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

### [ ] F2.1 — Dominio de normalización

- **Objetivo:** convertir cualquier payload observado en un esquema interno único y determinista.
- **Alcance:** `app/listings/vocab.py` (enums `FuelType`, `Transmission`, `SellerType`, `ListingStatus`, `EntryChannel`, `ProviderKind` y mapas de alias de marca), `NormalizedListing` (Pydantic, no ORM) con los campos del Plan Maestro §11, y `normalize(raw, source) -> NormalizedListing` puro con `payload_hash`.
- **Dependencias:** cierre de Fase 1.
- **Criterios de aceptación:** función pura sin I/O; dinero en `Decimal`; rangos validados (año, km, precio); campos no resolubles quedan `None` sin inventar; `payload_hash` estable ante reordenación de claves.
- **Pruebas necesarias:** unit `test_normalizer.py` (≈15 casos: enums, alias, Decimal, rangos inválidos, ausencias, estabilidad de hash, idempotencia).
- **Documentación afectada:** `docs/domain/data-model.md`.

### [ ] F2.2 — Persistencia y migraciones

- **Objetivo:** materializar `VehicleListing`, `RawListingPayload`, `ListingSnapshot`, `Source`, `SourceComplianceReview` y `SourceSyncRun`.
- **Alcance:** modelos SQLAlchemy 2.0 en `app/listings/models.py` y `app/sources/models.py`; migración de esquema `20260906_0002_search_listings.py`; migración de datos `20260906_0003_seed_sources.py` (filas `mock` y `manual` + compliance reviews) idempotente y con downgrade.
- **Dependencias:** F2.1.
- **Criterios de aceptación:** unique `(source_id, external_id)` en listings y `(source_id, payload_hash)` en payloads; dinero `Numeric(12,2)` + moneda; timestamps UTC; índices por consultas reales; `upgrade`/`downgrade` simétricos; esquema/datos separados (§38).
- **Pruebas necesarias:** integración `test_migration_0002.py` (base vacía → head; head → 0001 → head; schema esperado); seed idempotente.
- **Documentación afectada:** `docs/domain/data-model.md`, [ADR-0012](docs/adr/0012-listing-ingestion-and-dedup.md).

### [ ] F2.3 — Contratos de adquisición y conectores Mock/Manual

- **Objetivo:** implementar `Search Engine → Connector → Provider → Normalizer` (ADR-0006) solo con fuentes permitidas.
- **Alcance:** `BaseConnector` ABC (`search`, `fetch`, `health_check`), tipos de contrato (`RawListing`, `ConnectorSearchPage`, `ConnectorHealth`, `TransientConnectorError`), `MockConnector` con catálogo `catalog_v1.json` (~40 anuncios ES realistas, filtros marca/modelo/año/precio/combustible/km/provincia/seller_type, paginación, latencia y errores transitorios deterministas y desactivables), `ManualEntryConnector` (`build_raw`, `search` vacío), y `registry.py` con solo `mock` + `manual`.
- **Dependencias:** F2.1.
- **Criterios de aceptación:** contrato común real; MockConnector determinista (misma query ⇒ mismo resultado); ningún connector de portal real activo; catálogo versionado y anonimizado.
- **Pruebas necesarias:** unit `test_mock_connector.py`, `test_manual_connector.py`, `test_connector_registry.py`.
- **Documentación afectada:** `docs/source-compliance.md`, `docs/architecture/architecture.md`.

### [ ] F2.4 — Servicio de ingesta y deduplicación

- **Objetivo:** persistir lo observado de forma idempotente y trazable.
- **Alcance:** `app/listings/service.py` (`_ingest_raw` transaccional: normaliza → busca `(source_id, external_id)` → crea / refresca `last_seen_at` si `payload_hash` ya visto / actualiza + `ListingSnapshot` si cambió precio·km·estado·hash de descripción), `repository.py` con filtro + paginación.
- **Dependencias:** F2.2, F2.3.
- **Criterios de aceptación:** re-sync sin duplicados; snapshot solo ante cambio real; `RawListingPayload` nunca se modifica; dedup por `payload_hash` + `(source_id, external_id)` (ADR-0012).
- **Pruebas necesarias:** unit `test_listing_service.py`; integración `test_ingestion_flow.py` (PG real: crea N, re-sync = 0 duplicados y `last_seen_at` avanza, cambio de precio ⇒ nuevo snapshot).
- **Documentación afectada:** [ADR-0012](docs/adr/0012-listing-ingestion-and-dedup.md).

### [ ] F2.5 — API de fuentes, health y sincronización

- **Objetivo:** operar y observar las fuentes permitidas.
- **Alcance:** `app/sources/service.py` y `router.py`; `GET /sources`, `GET /sources/{key}/health`, `POST /sources/{key}/sync` (CSRF; `mode=sync` por defecto, `mode=async` encola actor Dramatiq), `GET /sources/{key}/sync-runs`; actor `sync_source_actor` idempotente por `run_id` en `app/sources/tasks.py` registrado en `app/worker.py`.
- **Dependencias:** F2.4.
- **Criterios de aceptación:** roles `OWNER|ADMIN` para `sync`; `SourceSyncRun` con estado y contadores; error saneado sin trazas; actor idempotente; una fuente caída no afecta a otras.
- **Pruebas necesarias:** unit `test_sources_service.py`, `test_sync_actor.py`; integración `test_sync_api.py`.
- **Documentación afectada:** `docs/architecture/data-flow.md`, `docs/api/openapi.json`.

### [ ] F2.6 — API de listings

- **Objetivo:** exponer búsqueda, detalle y alta manual de anuncios normalizados.
- **Alcance:** `app/search/schemas.py` (`SearchFilter` extensible), `app/listings/router.py`; `GET /listings` (filtros + paginación `{items,page,page_size,total,has_more}`), `GET /listings/{id}` (+ snapshots recientes), `POST /listings/manual` (CSRF, `OWNER|ADMIN`); regeneración de `docs/api/openapi.json`.
- **Dependencias:** F2.4.
- **Criterios de aceptación:** DTOs nunca exponen `payload` ni `payload_hash` (§36); 404 uniforme; alta manual valida procedencia y devuelve 409 ante duplicado `(manual, external_id)`; `VIEWER` no puede mutar (403); OpenAPI sincronizado en CI (`git diff --exit-code`).
- **Pruebas necesarias:** unit `test_search_filter.py`; integración `test_listings_api.py`, `test_manual_listing_api.py`; contract OpenAPI.
- **Documentación afectada:** `docs/api/openapi.json`, `docs/architecture/architecture.md`.

### [ ] F2.7 — Frontend de búsqueda y adquisición

- **Objetivo:** explorar anuncios mock, filtrarlos y registrar vehículos manualmente.
- **Alcance:** shell autenticado con navegación por teclado (`features/shell/app-shell.tsx`, landing `Anuncios`); `features/listings/` (`listings-view` con filtros RHF+Zod, tarjetas, paginación, botón "Sincronizar Mock", estados loading/empty/error/success; `manual-listing-form`; `listing-detail` con histórico de snapshots); primitivos `select`, `field`, `badge`; `features/system/status-view` (Estado como segunda pestaña).
- **Dependencias:** F2.5, F2.6.
- **Criterios de aceptación:** validación Zod espejo del servidor sin duplicar reglas críticas; TanStack Query por filtro; navegación por teclado; contraste; sin dependencia solo del color; cada pantalla nueva pasa `axe`.
- **Pruebas necesarias:** Vitest + Testing Library + `vitest-axe` para cada vista y formulario.
- **Documentación afectada:** `README.md`.

### [ ] F2.8 — Testing, calidad y DoD de Fase 2

- **Objetivo:** cerrar los gates de la fase.
- **Alcance:** `ruff format`/`ruff check`/`mypy --strict`; `pytest` unit + integración (PG y Redis reales); `prettier`/`eslint`/`tsc`/`vitest` (≥80% back y front, ramas críticas ≥ objetivo); build Next.js; E2E `tests/e2e/listings.spec.ts` (login → Anuncios → sincronizar → filtrar → alta manual → ver el anuncio); Semgrep/Gitleaks/pip-audit/pnpm audit sin HIGH/CRITICAL abiertos.
- **Dependencias:** F2.1–F2.7.
- **Criterios de aceptación:** todos los lanes aplicables en verde o no-aplicable justificado; sin regresiones sin registrar; cobertura ≥ umbral.
- **Pruebas necesarias:** matriz completa ejecutada y registrada.
- **Documentación afectada:** `docs/testing/testing-strategy.md`.

### [ ] F2.9 — Despliegue y validación en NAS

- **Objetivo:** dejar Fase 2 desplegada y saludable en el NAS.
- **Alcance:** `tar` + `scp` + `docker-compose build api web worker` + `up -d` + `exec api alembic upgrade head` (0002 y 0003) según `Guia_Conexion_ssh_NAS.md`; smoke test de login, sync Mock, listado y alta manual en `http://192.168.1.3:3080`.
- **Dependencias:** F2.8 y CI en verde.
- **Criterios de aceptación:** 6 contenedores saludables; migraciones aplicadas; smoke test correcto; sin tocar otros proyectos del NAS.
- **Pruebas necesarias:** smoke manual documentado; `docker-compose ps` y healthchecks.
- **Documentación afectada:** `docs/operations/deployment.md`.

### [ ] F2.10 — Documentación de Fase 2

- **Objetivo:** que la documentación refleje el estado real.
- **Alcance:** `docs/domain/data-model.md`, `docs/architecture/architecture.md`, `docs/architecture/data-flow.md`, `docs/source-compliance.md`, `docs/testing/testing-strategy.md`, `docs/adr/0012-*` y `docs/adr/README.md`, `README.md`, `implementation_plan.md`, este `task.md`.
- **Dependencias:** F2.1–F2.9.
- **Criterios de aceptación:** cambios de comportamiento y de documentación en el mismo conjunto de commits; enlaces válidos; informe de cierre de Fase 2.
- **Pruebas necesarias:** revisión de consistencia y de enlaces.
- **Documentación afectada:** toda la anterior.

## Fases posteriores — no autorizadas en este cambio

- [ ] Fase 3 — Vehicles y market data.
- [ ] Fase 4 — Knowledge Base.
- [ ] Fase 5 — Scoring y opportunities.
- [ ] Fase 6 — Watchlist e inspección.
- [ ] Fase 7 — Garage y finance.
- [ ] Fase 8 — Hardening.
- [ ] Fase 9 — Release MVP.

No se iniciará Fase 3 sin aprobación explícita del usuario.
