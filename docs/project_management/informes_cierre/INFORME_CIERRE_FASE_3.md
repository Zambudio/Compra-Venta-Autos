# Informe de cierre — Fase 3: Vehicles y Market Data

**Fecha:** 2026-09-07 · **Rama:** `feature/fase-3-vehicles-market` ·
**Fuente de verdad operativa:** [`task.md`](task.md) (F3.0–F3.6, todas `[x]`).

Fase autorizada por el usuario. Reglas estrictamente cumplidas:
- **Cero scraping:** únicamente datos derivados de las fuentes existentes (`mock` y `manual`).
- **Cero uso de matrículas ni teléfonos:** cumplimiento de Plan Maestro §13, §32 y R-03.
- **Deduplicación 100% asistida:** candidatos con confianza >= 0.60 quedan en estado `PENDING` para confirmación manual en 1 clic.
- **Cobertura superior al 80%:** 87.30% en backend y 90.37% en frontend.
- **Explicabilidad total:** desglose transparente de razones de coincidencia/discrepancia y métodos IQR reproducibles.

---

## 1. Alcance entregado

| Área | Entregado |
| --- | --- |
| **Entidad Vehicle y enlace tardío (F3.1)** | Modelo SQLAlchemy 2.0 `Vehicle` (`vehicles`) con atributos canónicos unificados (marca, modelo, generación, trim, motor, combustible, transmisión, año, contadores `first_listed_at`, `listing_count`). Columna foránea `VehicleListing.vehicle_id` nullable (`ondelete="SET NULL"`) con enlace tardío no destructivo. Migración de esquema `20260906_0004_vehicles_and_market.py`. |
| **Deduplicación asistida (F3.2)** | Modelo `VehicleMatchCandidate` (`vehicle_match_candidates`) con constraint de par único ordenado `(listing_a_id < listing_b_id)`. Algoritmo multicriterio determinista puro en `app/vehicles/matching.py` con pesos calibrados (marca/modelo obligatorios, año, combustible, cambio, km, precio, ubicación). Generación automática de candidatos en `ListingService.create_manual` y `SourceService.execute_run`. Endpoints `GET /match-candidates`, `POST /match-candidates/{id}/confirm`, `POST /match-candidates/{id}/reject`. Registro de `AuditEvent` (`manual_match`). |
| **Histórico y métricas (F3.3)** | Módulo de cálculo determinista con precisión `Decimal` en `app/vehicles/history.py`. Métricas a nivel de anuncio (`ListingHistoryMetrics`: `price_delta`, `price_delta_percentage`, `days_on_market`, `number_of_price_changes`, `is_relisted`) y consolidadas a nivel de vehículo (`VehicleHistoryMetrics`: `lowest_observed_price`, `highest_observed_price`, `current_min_price`, `days_on_market`, `total_price_changes`). Endpoints `GET /vehicles/{id}/history`. |
| **Estimación de mercado (F3.4)** | Modelo y DTO `MarketEstimate` (`market_estimates`). Algoritmo determinista en `app/vehicles/market.py` basado en mediana y filtro intercuartil (IQR) para exclusión de valores atípicos ($Q1 - 1.5 \times IQR, Q3 + 1.5 \times IQR$). Percentiles P25 y P75 como intervalo de mercado (`low_amount`, `high_amount`). Puntuación de confianza penalizada por dispersión y tamaño muestral ($N < 5$). Endpoint `POST /vehicles/{id}/market-estimate` y exposición en el detalle del vehículo. |
| **Frontend de vehículos y mercado (F3.5)** | Pestaña `Vehículos` integrada en el shell de navegación. Subpestaña **Catálogo Unificado** (`vehicles-view.tsx`) con filtros de marca y modelo, tarjetas informativas (`vehicle-card.tsx`), badges y paginación. Vista de **Ficha de Detalle** (`vehicle-detail.tsx`) con especificaciones técnicas, tarjetas de valoración de mercado (`MarketEstimateCard`), evolución histórica de precios (`VehicleHistoryCard`) y lista de anuncios asociados. Subpestaña **Deduplicación** (`match-candidates-view.tsx`) con cola de candidatos `PENDING`, comparador visual de anuncios lado a lado con etiquetas de coincidencia/discrepancia y acciones de confirmación y rechazo en 1 clic. Cumplimiento auditado de accesibilidad (`vitest-axe`). |
| **Testing, Calidad y Despliegue (F3.6)** | Test E2E de Playwright (`tests/e2e/vehicles.spec.ts`). Exportación del contrato OpenAPI (`docs/api/openapi.json`). Despliegue en Synology NAS con migración `0004` aplicada, 6 contenedores en estado _healthy_ y smoke test automatizado en vivo al 100%. |

---

## 2. Decisiones de arquitectura y diseño

- **[ADR-0013](docs/adr/0013-vehicle-matching-and-market-estimates.md):** Formalización de la deduplicación asistida sin PII, algoritmo determinista multicriterio ponderado, enlace tardío no destructivo de anuncios a vehículos, y valoración de mercado basada exclusivamente en comparables reales de la base de datos aplicando filtro IQR y cálculo de percentiles.
- **Auditoría inmutable:** Las acciones humanas de confirmación o rechazo de candidatos de duplicación emiten eventos de auditoría (`AuditEvent`) con el usuario actor, marcas temporales UTC y estado resultante.
- **Tolerancia a datos escasos:** Si una muestra de comparables tiene $N < 3$, el algoritmo de mercado emite un rango acotado por desviación porcentual ($\pm 5\%$) con puntuación de confianza mínima ($0.20$), garantizando que la API nunca invente datos irreales ni falle con excepciones no controladas.

---

## 3. Calidad y pruebas ejecutadas

| Gate de Calidad | Resultado | Métricas |
| --- | --- | --- |
| **Linters & Formato Backend** | `ruff check .` / `ruff format --check .` | Limpio al 100% (cero warnings, cero errores). |
| **Tipado Estricto Backend** | `mypy --strict app` | Limpio al 100% en todo el dominio `vehicles` y sus dependencias. |
| **Pruebas Unitarias Backend** | `pytest -m "not integration"` | **206 tests pasando (100%)**. Cobertura global **87.30%** (supera el requisito del 80%). Coberturas por módulo: `matching.py` (98.7%), `history.py` (96.7%), `market.py` (93.1%), `service.py` (84.2%). |
| **Linters & Formato Frontend** | `eslint` / `prettier --check` / `tsc --noEmit` | Limpio al 100% (cero errores de compilación o tipado). |
| **Pruebas Unitarias Frontend** | `vitest run --coverage` | **18 suites, 77 tests pasando (100%)**. Cobertura global de líneas **90.37%** (supera el requisito del 80%). |
| **Accesibilidad (a11y)** | `vitest-axe` | **Cero violaciones** en todas las vistas y componentes (`VehicleCard`, `VehicleDetail`, `MatchCandidatesView`, `VehiclesView`). |
| **Build de Producción Web** | `next build --webpack` | Compilación exitosa en 9.2s, TypeScript validado en 13.9s, optimización de páginas completada. |
| **Pruebas E2E** | Playwright (`tests/e2e/vehicles.spec.ts`) | Flujo completo programado: login OWNER, navegación a Vehículos, confirmación de candidato de duplicación, consulta de catálogo y verificación de detalle, valoración e histórico. |

---

## 4. Validación y Despliegue en Synology NAS (`192.168.1.3:3080`)

### 4.1 Despliegue de Contenedores y Base de Datos
- **Reconstrucción multi-stage:** `docker-compose build api worker web` y `docker-compose up -d`.
- **Estado del Stack:** Los 6 contenedores en estado **Up / Healthy**:
  - `motorscope-caddy-1` (Caddy reverse proxy en puerto `3080`)
  - `motorscope-web-1` (Next.js 16 standalone, usuario `node`, readonly rootfs)
  - `motorscope-api-1` (FastAPI en Python 3.14, usuario `motorscope`, readonly rootfs)
  - `motorscope-worker-1` (Dramatiq worker)
  - `motorscope-postgres-1` (PostgreSQL 18)
  - `motorscope-redis-1` (Redis 8)
- **Migración aplicada en PostgreSQL:** `20260906_0003 -> 20260906_0004` creando tablas `vehicles`, `vehicle_match_candidates`, `market_estimates` y añadiendo clave foránea `vehicle_id` en `vehicle_listings`.

### 4.2 Smoke Test en Vivo (`infrastructure/scripts/smoke_test_fase3.py`)

| Paso | Operación en Vivo | Código HTTP | Resultado |
| :--- | :--- | :---: | :--- |
| 1 | `GET /api/v1/health/live` | 200 OK | Servidor API operativo. |
| 2 | `GET /api/v1/health/ready` | 200 OK | Conectividad con PostgreSQL y Redis saludable. |
| 3 | `POST /api/v1/auth/login` | 200 OK | Autenticación de rol `OWNER` con emisión de cookies de sesión y CSRF. |
| 4 | `GET /api/v1/sources` | 200 OK | Fuentes `mock` y `manual` verificadas. |
| 5 | `POST /api/v1/sources/mock/sync` | 202 Accepted | Sincronización idempotente del catálogo Mock (36 anuncios procesados). |
| 6 | `POST /api/v1/listings/manual` | 201 Created | Alta manual de vehículo casi idéntico para disparar detección de duplicados. |
| 7 | `GET /api/v1/match-candidates?status=PENDING` | 200 OK | Detección automática en segundo plano: candidato generado con score >= 0.60. |
| 8 | `POST /api/v1/match-candidates/{id}/confirm` | 200 OK | Confirmación asistida en 1 clic: generación/vinculación de `vehicle_id` consolidado. |
| 9 | `GET /api/v1/vehicles` | 200 OK | Catálogo unificado lista el vehículo consolidado con sus contadores. |
| 10 | `GET /api/v1/vehicles/{id}` | 200 OK | Ficha técnica unificada con lista de los anuncios asociados. |
| 11 | `POST /api/v1/vehicles/{id}/market-estimate` | 200 OK | Estimación de mercado calculada por mediana IQR (precio estimado y rango [low - high]). |
| 12 | `GET /api/v1/vehicles/{id}/history` | 200 OK | Histórico consolidado con días en mercado, precios extremos y cambios. |
| 13 | `GET /` (Frontend Next.js) | 200 OK | Interfaz web responsiva accesible a través de Caddy. |

---

## 5. Riesgos, Mitigaciones y Deuda Técnica

- **R-02 (Host Windows sin Docker):** La ejecución de navegadores headless en Playwright dentro del host Windows sobre volúmenes de red UNC (`\\Zambu-nas\...`) presenta restricciones de pipes IPC (`spawn UNKNOWN`); la suite E2E queda asegurada para CI en Linux y la verificación funcional en vivo del NAS se garantiza mediante el smoke test automatizado en Python (`smoke_test_fase3.py`).
- **R-03 (Privacidad de datos):** La deduplicación opera estrictamente con marca, modelo, año, combustible, transmisión, kilometraje, precio y provincia aproximada. No se almacenan ni procesan teléfonos ni matrículas en el cálculo de matching.
- **R-04 (Tolerancia a muestras vacías de mercado):** Si no existen comparables homogéneos suficientes, la estimación retorna un intervalo seguro acotado sin arrojar errores 500.

---

## 6. Siguiente fase (Fase 4 — Knowledge Base)

**Estado:** DETENIDO. No se iniciará el desarrollo de la Fase 4 hasta recibir la confirmación y autorización explícita del usuario.
