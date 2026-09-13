# MotorScope

Plataforma privada para localizar, auditar y valorar oportunidades de vehículos de
ocasión. Usa un monolito modular con FastAPI, Next.js, PostgreSQL, Redis/Dramatiq,
Docker Compose y Caddy. Las decisiones de compra permanecen deterministas,
explicables y auditables.

## Estado del proyecto

**⏸️ Proyecto aparcado desde 2026-09-13** por decisión del propietario. Antes de
tocar nada, leer
[`docs/project_management/informes_cierre/INFORME_ESTADO_Y_RELEVO_2026-09-13.md`](docs/project_management/informes_cierre/INFORME_ESTADO_Y_RELEVO_2026-09-13.md):
resume el estado real de cada fase, un riesgo de cumplimiento legal abierto sobre el
conector Wallapop, la deuda de calidad conocida y los próximos pasos priorizados.

| Fase | Estado | Capacidad principal |
| --- | --- | --- |
| 0 — Planning | ✅ Completa | Arquitectura, roadmap, riesgos y ADRs. |
| 1 — Foundation | ✅ Completa | Auth, observabilidad, Docker, PostgreSQL, Redis y CI. |
| 2 — Search | ✅ Completa (conector Mock retirado en Fase 10) | Adquisición, normalización, ingesta y snapshots. |
| 3 — Vehicles | ✅ Completa | Vehicle/Listing, matching, histórico y comparables. |
| 4 — Knowledge | ✅ Completa | Evidencias, problemas conocidos y fiabilidad. |
| 5 — Scoring | ✅ Completa | Score versionado, valoración y oportunidades. |
| 6 — Watchlist/Inspección | ✅ Implementada | Seguimiento, inspección y fotos seguras. Sin tests frontend. |
| 7 — Garage/Finance | ✅ Implementada | Compra, ledger de gastos, venta y ROI. Sin tests frontend. |
| 8 — Hardening / 9 — Release | ⚠️ Autodeclarada, no verificada | Ver informe de relevo §3: falta evidencia de ASVS/DAST/restore real. |
| 10 — Wallapop real / 10.1 — Config dinámica y búsqueda en vivo | ✅ Implementada y desplegada (2026-09-13) | Conector real, toggle de fuentes, búsqueda en vivo con caché y rate limit. **Riesgo legal abierto**, ver informe. |

Desplegado y verificado en el Synology NAS el 2026-09-13 (6 contenedores
`healthy`, migración `20260913_0010`). Detalle completo, deuda de cobertura
frontend (`garage`/`watchlist` sin tests) y comandos de verificación en el informe
de relevo enlazado arriba.

## Capacidades actuales

- sesiones opacas, Argon2id, CSRF, roles y rate limiting;
- fuente Manual y conector real de Wallapop (ver riesgo de cumplimiento legal en el
  informe de relevo antes de reactivarlo);
- gestión dinámica de fuentes (activar/desactivar, salud, auditoría de cambios) y
  búsqueda en vivo con caché y rate limiting;
- anuncios normalizados, snapshots e ingesta idempotente;
- vehículos unificados, matching asistido e histórico de precio;
- comparables y estimación de mercado mediante mediana/IQR;
- Knowledge Base trazable con evidencias y clasificaciones;
- score de oportunidad versionado con 9 componentes explicables;
- estimación de costes, margen, ROI y presión del vendedor;
- Watchlist, inspección con checklist trazable y adjuntos seguros;
- Garage: compra, ledger de gastos append-only, venta, beneficio y ROI;
- workspace web responsive para anuncios, vehículos, Wiki, oportunidades, watchlist
  y garage.

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
[`docs/operations/Guia_Conexion_ssh_NAS.md`](docs/operations/Guia_Conexion_ssh_NAS.md)
y el mismo puerto `3080` para evitar colisiones con DSM.

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
- **Informe de relevo actual (leer primero):** [`docs/project_management/informes_cierre/INFORME_ESTADO_Y_RELEVO_2026-09-13.md`](docs/project_management/informes_cierre/INFORME_ESTADO_Y_RELEVO_2026-09-13.md)
- Estado operativo (desactualizado desde Fase 5, ver informe de relevo): [`docs/project_management/planificacion/task.md`](docs/project_management/planificacion/task.md)
- Secuencia y gates (desactualizado desde Fase 5): [`docs/project_management/planificacion/implementation_plan.md`](docs/project_management/planificacion/implementation_plan.md)
- Roadmap MVP/V2/V3: [`docs/project_management/planificacion/roadmap.md`](docs/project_management/planificacion/roadmap.md)
- Informe anterior (Fase 5, histórico): [`docs/project_management/informes_cierre/INFORME_ESTADO_Y_RELEVO_2026-09-12.md`](docs/project_management/informes_cierre/INFORME_ESTADO_Y_RELEVO_2026-09-12.md)
- Compliance de fuentes externas (ver riesgo Wallapop en el informe de relevo): [`docs/source-compliance.md`](docs/source-compliance.md)
- Arquitectura y dominio (cabeceras desactualizadas desde Fase 5): [`docs/architecture/`](docs/architecture/) y [`docs/domain/`](docs/domain/)
- ADRs: [`docs/adr/`](docs/adr/)
- Conexión y despliegue en el NAS: [`docs/operations/Guia_Conexion_ssh_NAS.md`](docs/operations/Guia_Conexion_ssh_NAS.md)
- Seguridad, testing y operaciones: [`docs/security/`](docs/security/), [`docs/testing/`](docs/testing/) y [`docs/operations/`](docs/operations/)

## Restricciones del MVP

No se permite scraping no autorizado, ML/LLM como decisor, datos mecánicos sin
evidencia, dinero en `float`, archivos en webroot ni infraestructura distribuida sin
necesidad demostrada y ADR previo.

Software privado. Prohibida su distribución sin autorización expresa.
