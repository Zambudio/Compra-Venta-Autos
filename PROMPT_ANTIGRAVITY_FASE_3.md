# Prompt de continuación para Antigravity — MotorScope, Fase 3

Hola. Vas a continuar el desarrollo de **MotorScope**, una plataforma web privada para
localizar, analizar y gestionar oportunidades de compra-venta de vehículos usados. Las
fases 0 (Planning), 1 (Foundation) y 2 (Search y Adquisición) ya están **completadas,
probadas y desplegadas**. Tu único objetivo ahora es ejecutar la **Fase 3 — Vehicles y
Market Data**. No avances a la Fase 4.

---

## 1. Ubicación y entorno

- **Directorio de trabajo:** `N:\IA\02_Proyectos\Compra-Venta Autos`
  (montado en red a `\\Zambu-nas\nas-drive-pedro\IA\02_Proyectos\Compra-Venta Autos`,
  que en el NAS es `/volume1/NAS-DRIVE-PEDRO/IA/02_Proyectos/Compra-Venta Autos`).
- **Repositorio:** `https://github.com/Zambudio/Compra-Venta-Autos.git`, rama `main`.
  Todo el trabajo de Fase 2 ya está en `origin/main`.
- **Contenedores:** el host Windows **no tiene Docker**. El stack corre en el
  **Synology NAS (`192.168.1.3`)**, desplegado vía Caddy en el puerto **`3080`**
  (`http://192.168.1.3:3080`). Guía operativa de SSH/rebuild en
  [`Guia_Conexion_ssh_NAS.md`](Guia_Conexion_ssh_NAS.md). El directorio de compose
  en el NAS es **el mismo recurso de red** que el directorio de trabajo, así que
  **no hace falta tar/scp**: basta `ssh nas-zambu`, `cd` al proyecto y
  `docker-compose build … && docker-compose up -d` (con guion; ruta completa
  `/volume1/@appstore/ContainerManager/usr/bin/docker-compose`, siempre con `sudo -n`).
- Servicios activos y _healthy_: `motorscope-caddy-1`, `motorscope-web-1`,
  `motorscope-api-1`, `motorscope-worker-1`, `motorscope-postgres-1`,
  `motorscope-redis-1`. La BD tiene el esquema en `head` (`20260906_0003`),
  el usuario OWNER (`owner@motorscope.com`) y 36 anuncios Mock deterministas.

## 2. Fuentes de verdad y reglas obligatorias

1. **Fuente principal:** [`PLAN_MAESTRO_VEHICULOS_SEGUNDA_MANO.md`](PLAN_MAESTRO_VEHICULOS_SEGUNDA_MANO.md).
   Léelo entero. Para Fase 3 son clave las secciones **§7 (Vehicle vs Listing),
   §12 (histórico de anuncios), §13 (deduplicación), §20 (market price),
   §42-43 (testing), §55 (Definition of Done)**.
2. **Fuente operativa:** [`task.md`](task.md). Añade el bloque **Fase 3** con tareas
   `F3.x` (objetivo, alcance, dependencias, criterios de aceptación, pruebas,
   documentación afectada, estado). Ninguna tarea se marca `[x]` sin superar sus
   criterios, pruebas y DoD.
3. **Plan y riesgos:** [`implementation_plan.md`](implementation_plan.md),
   [`roadmap.md`](roadmap.md).
4. **Decisiones arquitectónicas:** [`docs/adr/`](docs/adr/) (12 ADRs). Relevantes:
   [ADR-0005](docs/adr/0005-vehicle-listing-separation.md) (separación Vehicle/Listing),
   [ADR-0012](docs/adr/0012-listing-ingestion-and-dedup.md) (dedup de Fase 2; dice
   explícitamente que Fase 3 añade `VehicleListing.vehicle_id` nullable + workflow de
   matching, **sin migración destructiva**),
   [ADR-0010](docs/adr/0010-deterministic-versioned-score.md) (el score llega en Fase 5,
   no lo toques). Si tomas una decisión de arquitectura nueva, **crea ADR-0013** antes
   de implementar; no cambies el plan en silencio.
5. **Regla de scraping — INTACTA:** CERO scraping de portales reales. Fase 3 trabaja
   sobre datos **ya ingeridos** (Mock + Manual). No añadas conectores nuevos. Los
   comparables se calculan con los `vehicle_listings` que ya hay en la BD.
6. **Datos personales:** no introduzcas matrículas ni teléfonos como señal de
   deduplicación sin revisión legal previa (Plan §13, §32; riesgo R-03). Empieza el
   matching solo con marca/modelo/versión/año/km/ubicación/precio/descripción.
   El _perceptual hash_ de fotos es V2 (roadmap), no Fase 3.
7. **Autonomía:** trabaja de forma autónoma — ejecuta comandos, linters, tests y
   llamadas sin pedir confirmaciones innecesarias. Responde en **español**, conciso y
   técnico. Confirma solo antes de acciones difíciles de revertir (push, tocar datos
   de producción del NAS, borrar volúmenes).

## 3. Estado actual — qué existe ya (Fase 2)

### Backend (`apps/api`, FastAPI 0.141, Python 3.14, `uv`)

Módulos de dominio implementados: `core`, `auth`, `users`, `audit`, **`connectors`**,
**`listings`**, **`sources`**, **`search`**.

- `app/listings/vocab.py` — enums de dominio: `FuelType`, `Transmission`, `SellerType`,
  `ListingStatus`, `EntryChannel`, `ProviderKind`, `SyncRunStatus`; alias de marca y
  helpers `canonical_brand`, `parse_fuel_type`, etc. **Añade aquí los enums nuevos de
  Fase 3** (p. ej. `MatchStatus`, `MatchConfidence`, `MarketEstimateMethod`).
- `app/listings/normalizer.py` — `normalize(payload, source_key) -> NormalizedListing`
  (Pydantic, puro) + `payload_hash(dict) -> str`. `NormalizedListing` es el esquema
  interno único.
- `app/listings/models.py` — `VehicleListing` (único `(source_id, external_id)`),
  `RawListingPayload` (inmutable, único `(source_id, payload_hash)`), `ListingSnapshot`
  (append-only: precio, moneda, km, estado, `description_hash`, `observed_at`).
  **En Fase 3 añade `VehicleListing.vehicle_id` como FK nullable a `vehicles`.**
- `app/listings/service.py` — `ListingService`: `ingest_raw` (idempotente, dedup por
  `payload_hash` + `(source_id, external_id)`, snapshot solo ante cambio real vía
  `decide_ingest` puro), `search`, `get_detail`, `create_manual`.
- `app/listings/repository.py` — `ListingRepository.search` (join `Source`, filtros,
  orden, paginación), `get_with_snapshots`.
- `app/listings/schemas.py` — DTOs API (`ListingRead`, `ListingDetailRead`,
  `SnapshotRead`, `ListingPage`, `ManualListingCreate`). **Los DTOs NUNCA exponen
  `payload` ni `payload_hash`.**
- `app/listings/router.py` — `GET /listings`, `GET /listings/{id}`,
  `POST /listings/manual` (CSRF, rol `OWNER|ADMIN`, 409 duplicado).
- `app/connectors/` — `BaseConnector` ABC, `MockConnector`
  (`catalog_v1.json`, 36 anuncios), `ManualEntryConnector`, `registry.py`
  (solo `mock` y `manual`; `UnknownConnectorError` para el resto).
- `app/sources/` — `Source`, `SourceComplianceReview`, `SourceSyncRun` (modelos);
  `SourceService` (list/health/`create_run`/`execute_run` con reintentos de fallos
  transitorios); router `GET /sources`, `/sources/{key}/health`,
  `POST /sources/{key}/sync` (`mode=sync|async`), `/sources/{key}/sync-runs`;
  actor Dramatiq `sync_source_actor` idempotente por `run_id` en `app/sources/tasks.py`.
- `app/search/schemas.py` — `SearchFilter` (Pydantic, valida rangos; método
  `to_connector_filter`).
- `app/core/broker.py` — `configure_broker()` (Redis, perezoso). El worker importa
  `app/sources/tasks` para registrar los actores.
- **Migraciones:** `alembic/versions/20260906_0001…0003`. La **próxima es `20260906_0004`**.
  Enums con `sa.Enum(..., native_enum=False, create_constraint=True)`. Dinero
  `Numeric(12, 2)` + columna de moneda. `op.f()` para nombres. Migración de datos
  separada del esquema (§38).
- `app/models.py` registra **todos** los modelos para Alembic — añade ahí los nuevos.
- `app/main.py` incluye los routers con `prefix="/api/v1"`.
- **Contrato OpenAPI:** `uv run --project apps/api python infrastructure/scripts/export_openapi.py`
  regenera `docs/api/openapi.json`; CI valida con `git diff --exit-code`.

### Frontend (`apps/web`, Next.js 16 App Router, TS estricto, Tailwind 4)

- `src/features/shell/app-shell.tsx` — shell autenticado con pestañas
  (`Anuncios` por defecto, `Estado`) y navegación por teclado. **Añade aquí la pestaña
  nueva de Fase 3** (p. ej. `Vehículos`).
- `src/features/listings/` — `listings-view`, `filter-form`, `listing-card`,
  `listing-detail` (con histórico de snapshots), `manual-listing-form`, `api.ts`,
  `types.ts`, `format.ts` (formateadores es-ES + etiquetas de enums).
- `src/features/system/status-view.tsx` — estado Foundation.
- `src/components/ui/` — `button`, `input`, `select`, `field` (label+error accesible),
  `badge`. Tokens de color en `src/app/globals.css`.
- `src/lib/api.ts` — `apiRequest<T>(path, init)` (credenciales incluidas, maneja
  `ApiError`), `readCookie`.
- `src/test/render.tsx` — helper `renderWithClient` (QueryClient).
- Estado remoto con **TanStack Query**; formularios con **React Hook Form + Zod**.
  Nota: los `.transform()`/`z.coerce` de Zod chocan con el tipado de RHF +
  `exactOptionalPropertyTypes`; en `filter-form.tsx` se resuelve con esquema de
  strings + conversión manual en `submit`.

### Métricas de calidad de Fase 2 (mantener o superar)

- Backend: `ruff format`, `ruff check`, `mypy --strict` limpios; **159 tests unitarios,
  82.4% cobertura** (normalizador y conectores 100%); 23+ tests de integración
  (PostgreSQL/Redis reales, se ejecutan en CI).
- Frontend: `eslint`, `prettier`, `tsc --noEmit`, `next build --webpack` limpios;
  **56 tests (Vitest + `vitest-axe`), 91% stmts / 82% branches**.
- Umbral global obligatorio: 80% líneas/statements, 75% branches, 80% funciones.
  Autorización, normalización, **deduplicación, cálculos financieros/estadísticos**
  aspiran a ~100% de ramas.

## 4. Cómo ejecutar los gates (sin Docker en el host)

```powershell
# Backend (desde la raíz del repo)
uv run --project apps/api ruff format --check .
uv run --project apps/api ruff check .
uv run --project apps/api mypy app tests
uv run --project apps/api pytest -m "not integration"   # unit; requiere -p no:cacheprovider si el cache falla en UNC
uv run --project apps/api python infrastructure/scripts/export_openapi.py  # + git diff

# Frontend (DENTRO de apps/web; el cwd de invocación rompe vitest en unidades UNC)
cd apps/web
.\node_modules\.bin\eslint.cmd . --max-warnings=0
.\node_modules\.bin\tsc.cmd --noEmit
.\node_modules\.bin\prettier.cmd --check "src/**/*.{ts,tsx}" "tests/**/*.ts"
.\node_modules\.bin\vitest.cmd run --coverage
.\node_modules\.bin\next.cmd build --webpack
```

Los tests marcados `integration` y los E2E de Playwright **no se pueden ejecutar en
este host** (sin Docker). Se validan en **CI** (GitHub Actions: `ci.yml` levanta
PostgreSQL + Redis reales) y con **smoke test en el NAS**. Cuando cierres la fase:
`git push` y verifica que el run de CI queda en verde (`gh run watch`), luego rebuild
del NAS (`docker-compose build api web worker && up -d && exec api alembic upgrade head`)
y smoke test por Caddy con `curl` en `http://192.168.1.3:3080/api/v1/...`.

## 5. Método de trabajo

1. **Brainstorm + plan primero.** Lee `PLAN_MAESTRO`, `task.md`, ADRs. Escribe el
   desglose `F3.x` en `task.md` y, si hace falta, un ADR-0013. Presenta el diseño y
   confirma las 3-4 decisiones reales (naming, qué señales de matching, endpoint de
   revisión de candidatos, umbral de auto-confirmación) antes de implementar.
2. **Rama:** `feature/fase-3-vehicles-market` desde `main`. Commits incrementales por
   slice (rojo → verde → refactor, TDD). **No hagas push ni PR hasta que el usuario lo
   apruebe.** Mensajes de commit terminando en:
   ```
   Co-Authored-By: <tu identidntificador>
   ```
3. **TDD estricto:** test que falla → mínimo código para pasar → refactor. La lógica de
   deduplicación y de comparables/market estimate es crítica: sepárala en funciones
   puras testeables al 100% (como `decide_ingest` en Fase 2) y deja la orquestación
   con BD a los tests de integración.
4. **DoD por fase (§55):** formato, lint, tipos, unit, integración aplicable, frontend,
   E2E aplicable, migraciones probadas, seguridad sin HIGH/CRITICAL, documentación y
   ADRs al día, `task.md` reflejando el estado real. Emite
   `INFORME_CIERRE_FASE_3.md`.
5. Al terminar: **detente**. No inicies Fase 4 sin aprobación explícita del usuario.

## 6. Fase 3 — alcance (del Plan Maestro §7, §12, §13, §20)

### F3.1 — Entidad `Vehicle` y enlace tardío
- Modelo `Vehicle` (`vehicles`): identidad normalizada de un vehículo físico que puede
  aparecer en varios anuncios. Campos derivados/normalizados: marca, modelo,
  generación, versión/trim, código de motor, combustible, cambio, año, y agregados
  útiles (p. ej. `first_listed_at`, `listing_count`). UUID pk, timestamps UTC.
- `VehicleListing.vehicle_id`: FK **nullable** a `vehicles`, `ondelete SET NULL`. Un
  `Vehicle` tiene 1..* `VehicleListing`; un `VehicleListing` puede no tener `Vehicle`.
- Migración `20260906_0004` (esquema; solo `ADD COLUMN` nullable + tabla nueva, sin
  pérdida de datos). Sin migración de datos destructiva.

### F3.2 — Deduplicación asistida (§13)
- Modelo `VehicleMatchCandidate` (`vehicle_match_candidates`): par de anuncios (o
  anuncio ↔ vehicle), `confidence_score` (0..1 `Numeric`), `match_reasons` JSONB
  (señales que coinciden y su peso), `status` (`PENDING|CONFIRMED|REJECTED`),
  `decided_by_user_id` nullable, `decided_at` nullable. Único por par ordenado.
- Servicio de matching **determinista y explicable**: función pura
  `score_match(listing_a, listing_b) -> MatchResult(confidence, reasons)` con señales
  marca/modelo/versión/año/km/ubicación/precio/descripción (pesos configurables, sin
  ML). Umbral alto → candidato de alta confianza; umbral bajo → **requiere validación
  humana** (nunca se colapsa automáticamente por una sola señal).
- Job/servicio que, tras cada sync o alta manual, genera candidatos para los anuncios
  sin `vehicle` (idempotente).
- Endpoints: `GET /vehicles`, `GET /vehicles/{id}` (con sus listings y snapshots
  agregados), `GET /match-candidates?status=pending`,
  `POST /match-candidates/{id}/confirm` / `/reject` (CSRF, `OWNER|ADMIN`), que enlazan
  o separan `VehicleListing.vehicle_id` y registran `AuditEvent`
  (`manual_match` — ya previsto en el Plan §33).

### F3.3 — Histórico y métricas derivadas (§12)
- A partir de `ListingSnapshot` (ya existe, append-only), calcular **sin duplicar
  datos**: `price_delta`, `price_delta_percentage`, `days_on_market`,
  `number_of_price_changes`, precio inicial vs actual, detección de retirada/reaparición.
- Exponer en el detalle de `Listing` y de `Vehicle`. Frontend: gráfico/tabla de
  evolución de precio (accesible, no solo color).

### F3.4 — Comparables y `MarketEstimate` (§20)
- Modelo `MarketEstimate` (`market_estimates`): objetivo (`vehicle_id` o `listing_id`),
  `estimated_amount` + intervalo `low`/`high` (`Numeric` + moneda), `method`,
  `number_of_comparables`, `confidence` (crece con la cantidad y homogeneidad de
  comparables), `calculated_at`. **No inventa un valor de mercado**: se calcula con
  comparables reales (mismo modelo/generación, motor similar, año y km similares, zona).
- Servicio `estimate_market_price(vehicle|listing) -> MarketEstimate` determinista;
  guardar siempre `market_estimate_confidence` y `number_of_comparables`.
- Endpoint `GET /vehicles/{id}/market-estimate` (recalcula o devuelve el último).
  Separar claramente **observado / calculado / estimado / inferido** en el DTO y en la UI.

### F3.5 — Frontend
- Pestaña `Vehículos` en `app-shell`: lista de vehículos normalizados con nº de
  anuncios y estimación de mercado; detalle con anuncios enlazados, histórico de
  precio y `MarketEstimate` (intervalo + confianza, nunca como certeza).
- Vista de **revisión de candidatos de match** (cola `PENDING`, confirmar/rechazar,
  mostrando las señales que coinciden).
- Componentes accesibles, validación Zod, TanStack Query, tests + `vitest-axe`.

### F3.6 — Testing, calidad, despliegue y docs
- Tests unitarios de `score_match` y `estimate_market_price` (funciones puras, ~100%
  ramas); integración PostgreSQL real para el enlace `vehicle_id`, generación de
  candidatos, confirm/reject y comparables; frontend + E2E (`vehicles.spec.ts`:
  sincronizar → revisar candidato → confirmar → ver vehículo con histórico y
  estimación).
- Regenerar `docs/api/openapi.json`. Actualizar `docs/domain/data-model.md`,
  `docs/architecture/architecture.md`, `docs/architecture/data-flow.md`,
  `docs/testing/testing-strategy.md`, `README.md`, `implementation_plan.md`, `task.md`.
- Migración `20260906_0004` aplicada en el NAS; smoke test en vivo. `INFORME_CIERRE_FASE_3.md`.

### Fuera de Fase 3 (Fase 4+, NO tocar)
Knowledge Base / evidencias / clasificación WHITE/WATCH/BLACK (Fase 4);
Opportunity Score y valoración económica de compra (Fase 5); watchlist, inspección,
garage, finanzas (Fases 6-7); perceptual hash de fotos, matrícula/teléfono como señal,
feeds oficiales (V2).

---

## 7. Nota sobre el estado de git / CI

Fase 2 completa está en `origin/main` (hasta el commit `4197f62`, "fix(ci): …"). El
pipeline nunca había corrido entero hasta ahora; al cerrarse Fase 2 se corrigieron
varios fallos **preexistentes** (orden `pnpm/action-setup` vs `setup-node`, tests de
migración síncronos, base URL/navegador de Playwright, `exclude-newer` de uv, `pip`
fuera de la imagen runtime). Todo está registrado en
`implementation_plan.md → Fallos de CI detectados y corregidos` y en
`INFORME_CIERRE_FASE_2.md`.

**PASO 0 obligatorio antes de tocar Fase 3:**
1. `git pull` en `main`.
2. Ejecuta los gates locales (sección 4) — deben estar verdes.
3. `gh run list --branch main --limit 3` y `gh run view <id>` del último CI y Security.
   Si algún job sigue rojo (puede quedar alguna iteración de E2E o del escaneo de
   contenedores), **arréglalo como primera tarea** y deja el pipeline en verde antes
   de empezar F3.1. Los fallos, si los hay, serán de infraestructura de CI, no del
   código de dominio (backend y frontend ya pasan).
4. Rebuild del NAS si cambia algo de `apps/api`, `apps/web` o los Dockerfiles.

Luego empieza leyendo `PLAN_MAESTRO_VEHICULOS_SEGUNDA_MANO.md` y `task.md`, y presenta
el plan de Fase 3.
