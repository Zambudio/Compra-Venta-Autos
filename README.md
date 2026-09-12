# MotorScope

Plataforma privada para localizar, auditar y valorar oportunidades de vehículos de
ocasión. Usa un monolito modular con FastAPI, Next.js, PostgreSQL, Redis/Dramatiq,
Docker Compose y Caddy. Las decisiones de compra permanecen deterministas,
explicables y auditables.

## Estado del proyecto

| Fase | Estado | Capacidad principal |
| --- | --- | --- |
| 0 — Planning | ✅ Completa | Arquitectura, roadmap, riesgos y ADRs. |
| 1 — Foundation | ✅ Completa | Auth, observabilidad, Docker, PostgreSQL, Redis y CI. |
| 2 — Search | ✅ Completa | Mock/Manual, normalización, ingesta y snapshots. |
| 3 — Vehicles | ✅ Completa | Vehicle/Listing, matching, histórico y comparables. |
| 4 — Knowledge | ✅ Completa | Evidencias, problemas conocidos y fiabilidad. |
| 5 — Scoring | ✅ Completa funcionalmente | Score versionado, valoración y oportunidades. |
| 6 — Watchlist | ⏳ Siguiente | Seguimiento, inspección y fotos seguras. |
| 7–9 | ⏳ Pendientes | Garage/Finance, Hardening y Release MVP. |

La Fase 5 está desplegada en el Synology NAS con la migración `0006` y smoke 9/9.
La auditoría del 12-09-2026 detectó deuda de calidad pendiente antes de Fase 6: CI de
formato rojo, incidencias Ruff/mypy/ESLint/Prettier, cobertura frontend de ramas en
72,81% frente al 75% requerido y Trivy rojo para la imagen web. Véase
[`INFORME_ESTADO_Y_RELEVO_2026-09-12.md`](INFORME_ESTADO_Y_RELEVO_2026-09-12.md).

## Capacidades actuales

- sesiones opacas, Argon2id, CSRF, roles y rate limiting;
- fuentes Mock y Manual sin scraping de portales reales;
- anuncios normalizados, snapshots e ingesta idempotente;
- vehículos unificados, matching asistido e histórico de precio;
- comparables y estimación de mercado mediante mediana/IQR;
- Knowledge Base trazable con evidencias y clasificaciones;
- score de oportunidad versionado con 9 componentes explicables;
- estimación de costes, margen, ROI y presión del vendedor;
- workspace web responsive para anuncios, vehículos, Wiki y oportunidades.

## Arquitectura

```text
Navegador
   │
   ▼
Caddy :3080 ─────► Next.js
       └─────────► FastAPI /api/v1
                         ├── PostgreSQL
                         └── Redis ──► Dramatiq worker
```

Solo Caddy publica puertos. PostgreSQL es la fuente persistente; Redis contiene
estado efímero. El backend y el worker comparten el mismo paquete de dominio.

## Puesta en marcha con Docker

```bash
git clone https://github.com/Zambudio/Compra-Venta-Autos.git
cd Compra-Venta-Autos
cp .env.example .env
# Reemplaza las credenciales de ejemplo por secretos aleatorios.
docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose exec api python -m app.auth.cli create-owner
docker compose ps
```

Accesos predeterminados:

- Web: `http://localhost:3080`
- Liveness: `http://localhost:3080/api/v1/health/live`
- Readiness: `http://localhost:3080/api/v1/health/ready`
- OpenAPI/Swagger: `http://localhost:3080/docs`

En Synology se usa el binario indicado en
[`Guia_Conexion_ssh_NAS.md`](Guia_Conexion_ssh_NAS.md) y el mismo puerto `3080` para
evitar colisiones con DSM.

## Desarrollo local

Versiones principales fijadas en los lockfiles:

- Python 3.14, FastAPI 0.141.1, SQLAlchemy 2.0.52 y Alembic 1.19.2;
- Node.js 24.20.0, pnpm 11.1.3, Next.js 16.3.4 y React 19.2.8;
- PostgreSQL 18.6, Redis 8.8.2 y Caddy 2.10.

Backend, desde `apps/api`:

```powershell
uv sync --all-groups
uv run ruff format --check .
uv run ruff check .
uv run mypy app tests
uv run pytest -m "not integration" -p no:cacheprovider
```

Frontend, desde `apps/web` y preferiblemente mediante la unidad mapeada `N:` o `Z:`
en Windows:

```powershell
pnpm install --frozen-lockfile
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

Vitest puede resolver mal el proyecto cuando el directorio de trabajo es una ruta UNC;
usar `N:\IA\02_Proyectos\Compra-Venta Autos\apps\web` evita esa duplicación.

## Documentación

- Fuente principal: [`PLAN_MAESTRO_VEHICULOS_SEGUNDA_MANO.md`](PLAN_MAESTRO_VEHICULOS_SEGUNDA_MANO.md)
- Estado operativo: [`task.md`](task.md)
- Secuencia y gates: [`implementation_plan.md`](implementation_plan.md)
- Roadmap MVP/V2/V3: [`roadmap.md`](roadmap.md)
- Informe actual: [`INFORME_ESTADO_Y_RELEVO_2026-09-12.md`](INFORME_ESTADO_Y_RELEVO_2026-09-12.md)
- Prompt de relevo: [`PROMPT_CONTINUACION_FASE_6.md`](PROMPT_CONTINUACION_FASE_6.md)
- Arquitectura y dominio: [`docs/architecture/`](docs/architecture/) y [`docs/domain/`](docs/domain/)
- ADRs: [`docs/adr/`](docs/adr/)
- Seguridad, testing y operaciones: [`docs/security/`](docs/security/), [`docs/testing/`](docs/testing/) y [`docs/operations/`](docs/operations/)

## Restricciones del MVP

No se permite scraping no autorizado, ML/LLM como decisor, datos mecánicos sin
evidencia, dinero en `float`, archivos en webroot ni infraestructura distribuida sin
necesidad demostrada y ADR previo.

Software privado. Prohibida su distribución sin autorización expresa.
