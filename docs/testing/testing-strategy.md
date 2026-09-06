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
