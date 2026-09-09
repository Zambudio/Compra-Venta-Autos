# Informe de cierre — Fase 5: Scoring y Oportunidades

**Fecha:** 2026-09-09 · **Rama:** `feature/fase-5-scoring-opportunities` ·
**Fuente de verdad operativa:** [`task.md`](task.md) (F5.1–F5.6, todas `[x]`).

Fase completada bajo las reglas maestras del proyecto:
- **Cero LLM decisores y cero Machine Learning en el MVP (Plan Maestro §18):** motor de scoring 100% determinista, auditable y explicable basado en 9 componentes parametrizados que suman exactamente 1.000 (100%).
- **Versionado inmutable (Plan Maestro §18):** cada cálculo queda sellado a una versión inmutable del perfil (`ScoringProfileVersion`), garantizando reproducibilidad histórica permanente de cada oportunidad evaluada.
- **Modelo financiero con intervalos de confianza (Plan Maestro §19):** sin falsas certezas de rentabilidad; costes, márgenes y ROI proyectados como intervalos `[mín, máx]` en `Decimal` (EUR), basados en el marco fiscal español (ITP 4%, tasa de transferencia DGT 55,70€, preparación base 200€ y reparaciones mecánicas estimadas).
- **Presión del vendedor explicable (Plan Maestro §23):** detección objetiva basada en días en mercado y bajadas acumuladas de precio, sin especulaciones personales ni perfiles psicológicos inventados.
- **Accesibilidad estricta:** cero violaciones en `vitest-axe` y soporte para navegación completa por teclado.
- **Verificación real en vivo:** despliegue en Synology NAS (`192.168.1.3:3080`) con migración de base de datos aplicada y smoke test integral 100% exitoso.

---

## 1. Alcance entregado

| Área | Entregado |
| --- | --- |
| **ADR-0015 (F5.1)** | Formalización en [`docs/adr/0015-opportunity-scoring-and-economic-valuation.md`](docs/adr/0015-opportunity-scoring-and-economic-valuation.md) de la arquitectura del motor determinista de 9 componentes, pesos inmutables, valoración de costes e intervalos de rentabilidad. |
| **Modelos y migración de BD (F5.2)** | Modelos SQLAlchemy 2.0 `ScoringProfile`, `ScoringProfileVersion`, `OpportunityScore` y `Opportunity` en `apps/api/app/scoring/models.py`. Migración Alembic `20260909_0006_scoring_and_opportunities.py` con seed del perfil canónico `reventa-rapida` (v1). Tipos estrictos `Decimal` para importes y porcentajes. |
| **Motor de scoring y valoración económica (F5.3)** | Módulos puros `app/scoring/engine.py` y `app/scoring/valuation.py`. Cálculo de los 9 componentes (`price`, `reliability`, `liquidity`, `mechanical_risk`, `mileage`, `age`, `history`, `condition`, `listing_age`) con justificación explicativa por componente. Cálculo de estructura de costes, intervalos de margen [mín, máx], ROI [mín, máx], precio objetivo de compra sugerido (`target_purchase_price`) y presión del vendedor. |
| **Servicios y API REST (F5.4)** | `ScoringService` con orquestación completa para evaluación de anuncios (`evaluate_listing`) y vehículos (`evaluate_vehicle`), transiciones de estado de oportunidades (`IDENTIFIED`, `ANALYZING`, `VALIDATED`, `DISCARDED`, `PURCHASED`, `SOLD`), filtros avanzados por estado, score mínimo y marca. Enrutador `/api/v1/scoring` y `/api/v1/opportunities` protegido con RBAC y CSRF. Contrato OpenAPI regenerado en `docs/api/openapi.json`. |
| **Frontend: Mesa de Oportunidades y Widgets (F5.5)** | Módulo `apps/web/src/features/opportunities/` con `OpportunitiesView` (filtros reactivos, KPIs de mesa, paginación), `OpportunityCard` (tarjetas responsivas con selector de estado y acordeón expandible), `OpportunityScoreBreakdown` (panel de 9 componentes con barras de progreso y explicabilidad textual), `OpportunityValuationPanel` (estructura de costes ITP/DGT e intervalos de margen y ROI), y `VehicleOpportunityWidget` integrado en la ficha de vehículo (`VehicleDetail`). Nueva pestaña `Oportunidades` en la barra de navegación. |
| **Testing, Calidad y Despliegue en NAS (F5.6)** | Despliegue en el Synology NAS (`192.168.1.3:3080`). Migración `0006` aplicada en PostgreSQL 18. Script `smoke_test_fase5.py` ejecutado en vivo superando 9 de 9 fases (100% OK), validando la evaluación de anuncios, cálculo de los 9 componentes, modelo de costes español, evaluación de vehículo, cambio de estado a `VALIDATED` y respuesta HTTP 200 en frontend. |

---

## 2. Decisiones de arquitectura y diseño

- **[ADR-0015](docs/adr/0015-opportunity-scoring-and-economic-valuation.md):** Motor multicriterio determinista y valoración económica con intervalos.
- **Explicabilidad componente a componente:** Cada una de las 9 dimensiones devuelve obligatoriamente su peso, subpuntuación sobre 100, puntos ponderados aportados y un texto descriptivo del por qué (`reason`), eliminando cajas negras y permitiendo auditar cada decisión de compra.
- **Marco de costes realista España:** Considera explícitamente el Impuesto sobre Transmisiones Patrimoniales (ITP medio 4%), las tasas oficiales de transferencia de la DGT (55,70€), gastos de reacondicionamiento/limpieza (200€) y reparaciones mecánicas estimadas desde la base de conocimiento de fiabilidad (Fase 4), evitando sorpresas financieras tras la compra.
- **Presión del vendedor objetiva:** Basada exclusivamente en métricas demostrables (días transcurridos en mercado y número/porcentaje de rebajas registradas en snapshots históricos), sin suposiciones infundadas.

---

## 3. Calidad y pruebas ejecutadas

| Gate de Calidad | Resultado | Métricas |
| --- | --- | --- |
| **Linters & Formato Backend** | `ruff check` / `ruff format --check` | Limpio al 100% (cero errores, cero advertencias). |
| **Pruebas Unitarias Backend** | `pytest apps/api/tests/unit/` | **254 tests pasando (100%)**. Cobertura global **87.80%** (supera el umbral del 80%). Coberturas clave de Fase 5: `engine.py` (92%), `valuation.py` (99%), `schemas.py` (99%), `models.py` (100%), `vocab.py` (100%), `router.py` (85%). |
| **Linters & Formato Frontend** | `tsc --noEmit` / `vitest` | Limpio al 100%. TypeScript validado en build sin ningún error. |
| **Pruebas Unitarias Frontend** | `vitest run src/features/opportunities` | **4 suites de tests, 10 tests pasando (100%)**. |
| **Accesibilidad (a11y)** | `vitest-axe` | **Cero violaciones** en todas las vistas (`OpportunityScoreBreakdown`, `OpportunityValuationPanel`, `OpportunityCard`, `OpportunitiesView`). |
| **Build de Producción Web** | `next build --webpack` | Compilación exitosa, 5 páginas estáticas generadas sin incidencias. |
| **Smoke Test en NAS** | `python infrastructure/scripts/smoke_test_fase5.py` | **9 de 9 fases superadas al 100%** contra el entorno real en el Synology NAS. |

---

## 4. Validación y Despliegue en Synology NAS (192.168.1.3:3080)

### 4.1 Despliegue de Contenedores y Base de Datos
- **Reconstrucción de imágenes:** `docker-compose build api worker web` y `docker-compose up -d`.
- **Estado del Stack:** Los 6 contenedores en estado **Up / Healthy**:
  - `motorscope-caddy-1` (Caddy reverse proxy en puerto 3080)
  - `motorscope-api-1` (FastAPI backend en Python 3.14)
  - `motorscope-web-1` (Next.js 16 frontend)
  - `motorscope-worker-1` (Dramatiq worker)
  - `motorscope-postgres-1` (PostgreSQL 18)
  - `motorscope-redis-1` (Redis 8)
- **Migración aplicada:** `20260907_0005 -> 20260909_0006` en PostgreSQL del NAS.

### 4.2 Verificación E2E en Vivo (`smoke_test_fase5.py`)
1. **Health checks:** `/api/v1/health/live` y `/api/v1/health/ready` respondiendo 200 OK.
2. **Autenticación OWNER:** Login correcto con sesión persistida y token CSRF.
3. **Perfiles de scoring:** Perfil por defecto `reventa-rapida` (v1) verificado con 9 componentes que suman exactamente 1.000 (100%).
4. **Evaluación de anuncio:** Anuncio ŠKODA Octavia 2014 evaluado con éxito (Score total 67.95/100, presión de vendedor LOW).
5. **Valoración económica:** Coherencia de costes verificada: coste mín <= coste máx (7.327,70€), margen neto proyectado y precio sugerido de compra rápida (4.259,50€ para asegurar ROI objetivo).
6. **Evaluación de vehículo:** Oportunidad calculada a nivel de vehículo canónico ŠKODA Octavia con score idéntico coherente.
7. **Ciclo de vida y filtros:** Transición de estados `IDENTIFIED` -> `ANALYZING` (con notas de auditoría) -> `VALIDATED`. Filtro reactivo `?status=VALIDATED` recuperando la oportunidad con éxito.
8. **Frontend Web:** HTTP 200 en `http://192.168.1.3:3080/` con interfaz web lista para operación.

---

## 5. Próximos pasos (Fase 6 — Pendiente de autorización)

Queda pendiente de autorización explícita del usuario el inicio de la **FASE 6 — WATCHLIST E INSPECCIÓN**:
- Modelo `WatchlistEntry` con umbrales de alerta y seguimiento de precios.
- Checklists de inspección física estructurados (checks genéricos y específicos según afecciones conocidas del modelo).
- Registro de evidencias fotográficas in situ y calibración de estado previo a compra.

> **Regla de parada:** El sistema se detiene en este punto. No se iniciará ningún trabajo de la Fase 6 sin la aprobación explícita del usuario.
