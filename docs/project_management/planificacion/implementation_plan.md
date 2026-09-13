# Plan de implementación

Última actualización: 2026-09-12. `task.md` es la fuente operativa de verdad; este
documento conserva la secuencia, las dependencias y los gates del MVP.

## Estado actual

MotorScope tiene completas y desplegadas las fases 0–5. El producto ya permite:

```text
login → adquisición Mock/Manual → anuncios normalizados → vehículo unificado
      → histórico/comparables → Knowledge Base → score explicable → oportunidades
```

El `HEAD` auditado es `3e93e3c` en `main`, sincronizado con `origin/main`. La última
migración es `20260909_0006_scoring_and_opportunities.py`; el informe de Fase 5
registra despliegue en el NAS y smoke 9/9.

La siguiente capacidad funcional es Watchlist e Inspección, pero antes hay que
recuperar el baseline de calidad: el CI actual está rojo por formato, el frontend no
alcanza el umbral de cobertura de ramas y quedan incidencias de lint, tipos y Trivy.

## Progreso por fase

| Fase | Estado | Entrega / gate |
| --- | --- | --- |
| 0 | ✅ Completa | Inspección, alcance, documentación, riesgos y ADRs. |
| 1 | ✅ Completa | Monorepo, auth, PostgreSQL, Redis, Docker, observabilidad y CI. |
| 2 | ✅ Completa | Search, Mock/Manual, normalización, ingesta y snapshots. |
| 3 | ✅ Completa | Vehicle/Listing, matching asistido, histórico y market estimate. |
| 4 | ✅ Completa | Knowledge Base, evidencias, problemas y clasificaciones. |
| 5 | ✅ Completa funcionalmente | Scoring versionado, valoración y oportunidades; NAS smoke 9/9. El baseline de calidad requiere saneamiento. |
| 6 | ⏳ Siguiente | Watchlist, seguimiento de precio, inspección y fotos seguras. |
| 7 | ⏳ Pendiente | Compra, Garage, ledger, venta, beneficio y ROI real. |
| 8 | ⏳ Pendiente | Hardening ASVS L2, DAST, rendimiento y restore probado. |
| 9 | ⏳ Pendiente | Release reproducible y aceptación completa del MVP. |

## Evidencia de la auditoría de 2026-09-12

| Gate | Resultado actual |
| --- | --- |
| Backend unit tests | ✅ 254/254; cobertura total 85,42%. |
| Frontend tests | ✅ 109/109. |
| Frontend cobertura | ❌ ramas 72,81%; mínimo configurado 75%. Statements 84,64%, funciones 82,21%, líneas 87,78%. |
| TypeScript | ✅ `tsc --noEmit`. |
| Ruff | ❌ 17 incidencias y 4 archivos sin formato. |
| mypy strict | ❌ 13 errores en 7 archivos. |
| ESLint | ❌ 1 error y 13 warnings en oportunidades. |
| Prettier | ❌ 25 archivos no conformes. |
| CI de `main` | ❌ backend y frontend se detienen en formato; E2E no llega a ejecutarse. |
| Security de `main` | ⚠️ SAST, secretos, dependencias y CodeQL pasan; Trivy falla en la imagen web. |
| NAS Fase 5 | ✅ evidencia histórica: 6 contenedores saludables, migración `0006` y smoke 9/9. |

Los primeros fallos de pytest observados desde la raíz eran un problema de invocación:
sin usar `apps/api` como directorio de trabajo no se cargaba `pyproject.toml`. La
ejecución canónica desde `apps/api` pasa 254/254 y es la que cuenta.

## Orden de ejecución restante

### 1. F6.0 — Saneamiento del baseline

Resolver primero formato, Ruff, mypy, ESLint y Prettier; añadir pruebas dirigidas a
las ramas sin cubrir de oportunidades; revisar el hallazgo Trivy de la imagen web.
Regenerar OpenAPI y confirmar CI + Security completos, incluido E2E. No mezclar este
saneamiento con la migración funcional de Fase 6.

**Gate:** todos los lanes verdes o excepción de seguridad formal según §55 del Plan
Maestro. Este bloque debe ser uno o varios commits aislados y fáciles de revisar.

### 2. F6.1 — ADR-0016 y contratos

Definir antes del esquema:

- agregado `WatchlistEntry` y transiciones de estado;
- relación con `Opportunity`, `VehicleListing` y `Vehicle`;
- `Inspection` e `InspectionItem`, con snapshot inmutable del checklist generado;
- procedencia de cada check: genérico o `KnownIssue` trazable;
- puerto `FileStorage`, implementación local y autorización de adjuntos;
- política de retención, backup, eliminación y auditoría.

**Gate:** ADR aceptado, data model/data flow/threat model actualizados y casos de
prueba definidos. No introducir S3 ni notificaciones externas; son V2.

### 3. F6.2 — Watchlist vertical

Crear migración `0007`, modelos, schemas, servicio y API. El precio al guardar se
persiste como evidencia; el precio actual y su evolución se derivan del anuncio y sus
snapshots. Implementar notas privadas y estados `WATCHING`, `CONTACTED`,
`VISIT_PLANNED`, `INSPECTED`, `REJECTED`, `PURCHASED` con matriz de transiciones.

**Gate:** idempotencia, RBAC, CSRF, auditoría, constraints PostgreSQL y OpenAPI.

### 4. F6.3 — Inspección dinámica

Crear inspecciones vinculadas a una entrada de watchlist. Generar los checks genéricos
del Plan Maestro y añadir checks específicos para modelo/generación/motor/cambio a
partir de la Knowledge Base. Cada ítem admite `PASS`, `WARNING`, `FAIL` o
`NOT_CHECKED`, notas y adjuntos. El checklist queda congelado al crearse.

**Gate:** lógica determinista altamente cubierta, sin afirmaciones mecánicas sin
evidencia y sin mutación retroactiva de inspecciones cerradas.

### 5. F6.4 — Archivos seguros

Implementar `FileAttachment` y almacenamiento local fuera de webroot: nombres
internos aleatorios, allowlist de MIME comprobada por contenido, tamaño máximo, hash,
descarga autorizada, prevención de ejecución y eliminación controlada. Incorporar los
archivos al runbook de backup/restore.

**Gate:** tests negativos de MIME falso, tamaño, path traversal, autorización y
contenido corrupto; revisión ASVS V5.

### 6. F6.5–F6.6 — UI, E2E y despliegue

Añadir Watchlist e Inspección al workspace, empezando desde las oportunidades. La UI
debe cubrir loading/error/empty/success, teclado, mobile y axe. Cerrar con migración
en NAS, smoke del flujo completo, informe de Fase 6 y documentación sincronizada.

**Gate:** guardar oportunidad → registrar bajada de precio → planificar visita →
completar checklist → adjuntar foto → aceptar/rechazar, con 6 contenedores saludables.

### 7. Fase 7 — Garage y finance

1. Diseñar `OwnedVehicle`, `Expense`, `Sale` y adjuntos contractuales.
2. Convertir una oportunidad validada en compra mediante una transacción idempotente.
3. Implementar ledger append-only; no persistir totales derivados.
4. Registrar venta y calcular beneficio/ROI con `Decimal/Numeric`.
5. Entregar Garage, dashboard, permisos, migración, E2E y smoke NAS.

**Gate:** vertical slice financiero completo y conciliable: compra, todos los gastos y
venta producen un beneficio y ROI reproducibles.

### 8. Fase 8 — Hardening

Revisar ASVS 5.0 L2 requisito por requisito; actualizar threat model; ejecutar SAST,
secret scanning, audits, CodeQL, Trivy y DAST; revisar permisos/privacidad/retención;
medir accesibilidad y rendimiento; probar backup/restore, migración y rollback reales;
cerrar propietarios y runbooks operativos.

**Gate:** cero HIGH/CRITICAL sin resolver o excepción vigente, restore probado dentro
del RPO/RTO aprobado y staging listo para release.

### 9. Fase 9 — Release MVP

Congelar versión y alcance, producir artefactos reproducibles, validar migración desde
la versión desplegada, rollback, smoke y alertas. La aceptación final recorre:

```text
login → search → vehículo → wiki → score → watchlist → inspección
      → compra → gastos → venta → beneficio/ROI
```

## Riesgos activos

| ID | Riesgo | Estado / mitigación |
| --- | --- | --- |
| R-01 | Scraping no autorizado | Activo. Solo Mock/Manual hasta revisión formal por fuente. |
| R-02 | Entorno local sobre UNC | Mitigado parcialmente con `N:`/`Z:`; Vitest desde UNC duplica la ruta. Ejecutar frontend desde unidad mapeada. |
| R-03 | Datos personales y documentos | Activo. Minimización y política definitiva antes de F6.4/F7. |
| R-04 | Conocimiento/estimaciones incorrectas | Mitigado con evidencia, confianza y cálculos deterministas; mantener revisión humana. |
| R-05 | Dependencias recientes | Activo. Pins, lockfiles y CI; actualizar cooldown al regenerar locks. |
| R-06 | Restore no probado | Bloquea release; ejecutar en F8. |
| R-07 | Exposición de la aplicación privada | Activo. Auth default-deny, Caddy, red interna y revisión ASVS. |
| R-08 | Baseline de calidad rojo | Activo y prioritario. Resolver en F6.0 antes de nueva funcionalidad. |
| R-09 | Archivos maliciosos o fuga de fotos/documentos | Nuevo. FileStorage fuera de webroot, validación por contenido, RBAC y límites. |

## Reglas permanentes

- No scraping real sin compliance aprobado.
- No ML ni LLM como decisor; scoring y checklists deben ser explicables.
- No almacenar dinero en `float`, archivos binarios en PostgreSQL ni totales
  financieros duplicados.
- Toda migración se hace con Alembic y se prueba desde la versión anterior.
- Una fase no termina sin tests, calidad, seguridad, documentación, migración y smoke.
- Conservar los activos no versionados de `apps/web/public/brand/`; no pertenecen a
  esta auditoría y no deben borrarse ni incluirse sin revisar su procedencia.

## Punto de relevo

El siguiente agente debe comenzar por `PROMPT_CONTINUACION_FASE_6.md`, ejecutar F6.0
y detenerse si no puede recuperar un baseline verde. El desglose canónico está en
`task.md`; los informes `INFORME_CIERRE_FASE_3.md` a
`INFORME_CIERRE_FASE_5.md` son evidencia histórica, no sustituyen el estado actual.
