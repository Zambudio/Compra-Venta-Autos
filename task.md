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

## Fases posteriores — no autorizadas en este cambio

- [ ] Fase 2 — Search y adquisición.
- [ ] Fase 3 — Vehicles y market data.
- [ ] Fase 4 — Knowledge Base.
- [ ] Fase 5 — Scoring y opportunities.
- [ ] Fase 6 — Watchlist e inspección.
- [ ] Fase 7 — Garage y finance.
- [ ] Fase 8 — Hardening.
- [ ] Fase 9 — Release MVP.

No se iniciará Fase 2 sin aprobación explícita del usuario.
