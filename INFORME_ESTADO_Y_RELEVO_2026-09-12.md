# Informe de estado y relevo — 12 de septiembre de 2026

## Resumen

MotorScope ha completado funcionalmente 6 de sus 10 fases (0–5). El sistema llega
desde autenticación y adquisición controlada hasta una mesa de oportunidades con
valoración económica y score determinista. El siguiente bloque de producto es Fase 6,
Watchlist e Inspección; después quedan Garage/Finance, Hardening y Release MVP.

El estado desplegado de Fase 5 fue validado en el Synology NAS con 6 contenedores
saludables, migración `0006` y smoke test 9/9. Sin embargo, una auditoría nueva del
`HEAD` `3e93e3c` demuestra que la afirmación histórica “todos los gates limpios” ya no
describe el repositorio: los tests funcionales pasan, pero CI, formato, lint, tipos,
cobertura de ramas frontend y Trivy requieren atención inmediata.

## Avances entregados

| Fase | Resultado |
| --- | --- |
| 0 — Planning | Monorepo, roadmap, documentación base, riesgos y ADRs. |
| 1 — Foundation | FastAPI/Next.js, PostgreSQL, Redis/Dramatiq, Docker/Caddy, auth segura, observabilidad y CI. |
| 2 — Search | Fuentes Mock/Manual, normalización, ingesta idempotente, snapshots y frontend de anuncios. |
| 3 — Vehicles | Separación Vehicle/Listing, matching asistido, histórico, comparables y estimación IQR. |
| 4 — Knowledge | Catálogo técnico, fuentes/evidencias, problemas conocidos, clasificación y diagnóstico de fiabilidad. |
| 5 — Scoring | Perfil versionado, score de 9 componentes, costes/margen/ROI, presión del vendedor y oportunidades. |

Evidencias principales:

- migraciones Alembic `0001`–`0006` presentes;
- informes de cierre de Fases 2–5;
- scripts de smoke independientes para Fases 3, 4 y 5;
- módulos backend `vehicles`, `knowledge` y `scoring`;
- módulos web `vehicles`, `knowledge` y `opportunities`;
- `main` y `origin/main` apuntan a `3e93e3c`.

## Verificación ejecutada en esta auditoría

| Comprobación | Resultado |
| --- | --- |
| `pytest -m "not integration"` desde `apps/api` | 254 passed, 24 deselected, cobertura 85,42%. |
| Vitest desde `N:\...\apps\web` | 27 suites y 109 tests pasan. |
| Cobertura frontend | Falla el gate: ramas 72,81% frente a 75%; resto sobre umbral. |
| TypeScript | Pasa. |
| Ruff format/check | Falla: 4 archivos sin formato y 17 incidencias. |
| mypy strict | Falla: 13 errores en 7 archivos. |
| ESLint | Falla: 1 error y 13 warnings, concentrados en oportunidades. |
| Prettier | Falla: 25 archivos. |
| GitHub CI de `3e93e3c` | Falla en formato backend y frontend; E2E queda omitido por dependencia. |
| GitHub Security de `3e93e3c` | SAST/dependencias/secretos y ambos CodeQL pasan; Trivy falla en la imagen web. |

Nota operativa: ejecutar pytest desde la raíz con `uv run --project apps/api` no carga
la configuración de pytest como se espera en este entorno y produce falsos fallos
async. La invocación canónica es desde `apps/api`. Vitest debe ejecutarse desde una
unidad mapeada (`N:` o `Z:`), porque la ruta UNC se duplica durante la resolución.

## Lo que queda

### Prioridad 0 — recuperar la confianza del pipeline

F6.0 debe limpiar Ruff/Prettier, corregir mypy y ESLint, cubrir ramas de oportunidades,
regenerar OpenAPI y dejar CI completo en verde. También debe revisar el fallo Trivy de
la imagen web. Esta tarea no añade producto y debe mantenerse separada de Fase 6.

### Fase 6 — Watchlist e Inspección

- guardar oportunidades y seguir precio/estado/notas;
- estados desde `WATCHING` hasta `PURCHASED` o `REJECTED`;
- checklist genérico más checks específicos trazables desde Knowledge Base;
- resultados `PASS|WARNING|FAIL|NOT_CHECKED` y snapshot histórico;
- fotos mediante `FileStorage` local seguro, fuera de webroot;
- UI accesible, tests, migración `0007`, E2E, despliegue y smoke NAS.

### Fase 7 — Garage y Finance

- compra y creación de `OwnedVehicle` sin perder el histórico;
- ledger append-only de gastos y documentos;
- venta, beneficio y ROI calculados, no duplicados;
- dashboard, permisos, migración, E2E y smoke.

### Fase 8 — Hardening

- auditoría ASVS 5.0 L2 y threat model final;
- DAST, dependencias, imágenes, permisos, privacidad y retención;
- accesibilidad/rendimiento;
- backup/restore, migración y rollback reales y medidos.

### Fase 9 — Release MVP

- versión y artefactos reproducibles;
- despliegue/rollback verificados;
- smoke y alertas;
- aceptación del flujo completo hasta beneficio y ROI real.

## Decisiones que el siguiente agente debe fijar en ADR-0016

1. La identidad de Watchlist debe colgar de `Opportunity` y conservar referencias a
   listing/vehicle sin duplicar su información.
2. El precio al guardar se persiste; el actual y el histórico se derivan de snapshots.
3. El checklist se genera de forma determinista y se congela al crear la inspección.
4. Cada check específico conserva la referencia al `KnownIssue`/evidencia que lo
   originó.
5. Los binarios viven fuera de PostgreSQL y webroot detrás de un puerto `FileStorage`.
6. La transición a `PURCHASED` prepara Fase 7, pero no crea aún `OwnedVehicle`.

## Riesgos y observaciones

- El directorio `apps/web/public/brand/` contiene tres archivos no versionados. Se ha
  preservado intacto y no debe añadirse o borrarse sin revisar su procedencia/licencia.
- Los informes de cierre son evidencia del momento en que se emitieron; `task.md` y
  `implementation_plan.md` mandan para el estado actual.
- El restore sigue sin prueba real y bloquea el release, aunque no el desarrollo de F6.
- No se debe introducir scraping real, S3, notificaciones externas, ML ni LLM decisor.

## Documentación actualizada

- `task.md`: resumen verificable y desglose F6.0–F9.
- `implementation_plan.md`: secuencia, gates, riesgos y punto de relevo.
- `roadmap.md`: progreso del MVP.
- `README.md`: estado real, capacidades y comandos actuales.
- `docs/architecture/architecture.md` y `docs/domain/data-model.md`: cabeceras y
  módulos implementados sincronizados.
- `PROMPT_CONTINUACION_FASE_6.md`: instrucciones autocontenidas para el siguiente
  agente.
