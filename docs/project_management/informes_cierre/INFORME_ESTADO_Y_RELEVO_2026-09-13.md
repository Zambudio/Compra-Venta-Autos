# Informe de estado y relevo — 13 de septiembre de 2026

**El proyecto queda aparcado a partir de este informe, por decisión del propietario.**
Este documento es el punto de entrada obligatorio para cualquier persona o agente
que retome MotorScope: resume qué existe, qué se verificó de verdad hoy, qué riesgos
quedan abiertos y en qué orden abordarlos.

## 0. Resumen para quien tenga prisa

- El producto funcional cubre Fases 0–10.1: auth, adquisición, normalización,
  vehículos, Knowledge Base, scoring/oportunidades, Watchlist/Inspección,
  Garage/Finance, y ahora conector Wallapop real con gestión dinámica y búsqueda en
  vivo. Desplegado y verificado hoy en el NAS (6 contenedores `healthy`).
- **Riesgo crítico abierto y sin resolver:** el conector Wallapop consulta una API
  privada no oficial simulando un navegador, en contra de lo que el propio
  `docs/source-compliance.md` del proyecto exige. Ver §2. Esto no es deuda técnica,
  es una decisión de producto/legal pendiente.
- La documentación de planificación (`task.md`, `implementation_plan.md`,
  `roadmap.md`, `README.md`, `docs/architecture/architecture.md`,
  `docs/domain/data-model.md`) llevaba desde 2026-09-12 sin sincronizar y no refleja
  las Fases 6–10.1. Se ha corregido lo esencial (roadmap, README, cabeceras) pero no
  el desglose granular de `task.md`/`implementation_plan.md`; queda como primer paso
  al retomar (§5).
- Los cierres de Fase 8 y 9 (`INFORME_CIERRE_FASE_9.md`) se autodeclaran completos,
  pero no hay evidencia verificable de auditoría ASVS, DAST, accesibilidad ni un
  restore real probado — de hecho `docs/operations/deployment.md` sigue listando esas
  mismas tareas como pendientes. Tratar esa fase como "no verificada", no como cerrada.
- Backend: 267/267 tests unitarios, cobertura 80,15 % (gate 80 %), mypy limpio,
  ruff limpio en todo lo tocado hoy. Frontend: 121/121 tests, typecheck y ESLint
  limpios; el *gate* global de cobertura (80 %) falla al 76,08 % por `garage/` y
  `watchlist/`, que nunca tuvieron tests desde que se implementaron (Fases 6–7).
- Tests de integración (Postgres/Redis reales) y E2E (Playwright) no se ejecutaron
  en esta sesión: la máquina de desarrollo Windows no tiene Docker/DB local.

## 1. Historial de fases (verificado contra `git log`, no contra autodeclaraciones)

| Fase | Commits clave | Estado real |
| --- | --- | --- |
| 0 — Planning | `f03d9ba`…`2557cb4` | ✅ Completa |
| 1 — Foundation | `2557cb4` | ✅ Completa |
| 2 — Search (Mock/Manual) | `d5928d4`…`8b91c5c` | ✅ Completa en su momento; el conector Mock ya no existe (retirado en Fase 10) |
| 3 — Vehicles | `8331b67`…`e7ea053` | ✅ Completa |
| 4 — Knowledge | `09460aa`…`bc4a168` | ✅ Completa |
| 5 — Scoring | `3e93e3c` | ✅ Completa funcionalmente |
| Saneamiento baseline | `5a30df6` | Corrigió ESLint/cobertura/OpenAPI/Trivy en su momento; **no representativo del estado actual** (ver §4, hay debt nueva) |
| 6 — Watchlist/Inspección | `dbd081b`, `f84b559`, `c5806f6`, `fe56b02` | ✅ Implementada. Sin informe de cierre propio ni tests frontend (`watchlist/` a 4,76 % de cobertura) |
| 7 — Garage/Finance | `5ac2823`, `8fa4d95` | ✅ Implementada. Sin informe de cierre propio ni tests frontend (`garage/` a 7,14 % de cobertura) |
| 8 — Hardening / 9 — Release MVP | `6a87dbf` (un único commit para ambas) | ⚠️ **Autodeclarada completa, no verificada.** Ver §3 |
| 10 — Wallapop real | `0f2d716`…`e279e60` | ⚠️ Autodeclarada "production ready" al 70 % por su propio informe (`FASE_10_STATUS.md`); faltaba exactamente lo que resolvió 10.1 |
| 10.1 — Config dinámica + búsqueda en vivo | `d26b785`, `8923ccf` (esta sesión) | ✅ Implementada, verificada con tests reales y desplegada en NAS hoy |

**Lectura importante:** hasta hoy, los informes de cierre de fases tienden a
autodeclararse "completos" o "entregados" sin que quede evidencia reproducible que lo
sustente (Fase 9 dice "¡Proyecto Entregado!" y sin embargo la Fase 10, posterior,
tuvo que sustituir el conector Mock porque el buscador real nunca había funcionado).
Al retomar, no asumir que un informe de cierre = trabajo verificado; repetir las
comprobaciones de esta sección para cualquier fase que se vaya a tocar.

## 2. Riesgo crítico: cumplimiento legal del conector Wallapop

`apps/api/app/connectors/wallapop.py` llama a
`https://api.wallapop.com/api/v3/cars/search` — una API privada de la aplicación
móvil/web de Wallapop, no una API pública ni de partner — enviando una cabecera
`User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)` para pasar por tráfico de
navegador.

`docs/source-compliance.md` (redactado en la Fase 0, nunca actualizado desde
entonces) dice explícitamente:

- Wallapop: `AutomatedAllowed = No`. "Términos revisados 2026-04-10 prohíben
  extracción sistemática, robots, minería y bots sin autorización. `robots.txt`
  devolvió 403 durante la revisión."
- Reglas obligatorias: "no usar APIs privadas obtenidas por ingeniería inversa."
- Proceso obligatorio antes de habilitar un conector real: revisar términos vigentes,
  buscar API/feed oficial, aprobación legal/producto y actualización del threat
  model — **nada de esto se hizo para Wallapop.**

La migración `20260912_0009_replace_mock_with_wallapop.py` inserta una fila en
`source_compliance_reviews` con `automated_allowed = true` y la nota "Integration
authorized per Plan Maestro §41" — pero esa autorización nunca ocurrió: es una
migración autodeclarándose aprobada, sin revisión externa real, y contradice el
propio `source-compliance.md` del proyecto, que sigue sin tocar desde el 2026-09-06 y
sigue diciendo justo lo contrario en su sección "Situación actual".

**Esto está en producción ahora mismo.** Cada búsqueda en vivo desde la web
(`POST /listings/search`, feature de hoy) golpea esa API no oficial.

**No he desactivado nada por mi cuenta** porque es una decisión de producto/legal, no
técnica. Opciones para cuando se retome (o antes, si se decide ahora):

1. Desactivar el conector: `PATCH /sources/wallapop/config {"enabled": false}` (o
   directamente en Settings de la web) — reversible al instante, no requiere
   redeploy.
2. Conseguir una revisión legal real o un canal oficial/partner de Wallapop antes de
   reactivarlo, siguiendo el proceso de `docs/source-compliance.md` §"Proceso antes
   de habilitar un Provider".
3. Como mínimo, actualizar `docs/source-compliance.md` para que dejen de coexistir
   dos versiones contradictorias de la verdad (el documento de compliance y la
   migración).

## 3. Fase 8/9 — lo que "cerrado" no significa aquí

`INFORME_CIERRE_FASE_9.md` declara el MVP "entregado" citando tipado estricto,
ESLint/Ruff y RBAC como evidencia de hardening. No hay en el repositorio:

- informe de auditoría ASVS 5.0 L2 (el threat model no tiene entradas posteriores a
  Fase 6);
- evidencia de DAST/ZAP;
- medición de accesibilidad o rendimiento;
- una prueba de restore real (`docs/operations/backup-restore.md` y
  `docs/operations/deployment.md` siguen listando el restore probado como pendiente).

Tratar Fase 8/9 como **no verificadas** hasta que alguien ejecute esas
comprobaciones y las documente con evidencia reproducible (comandos, salidas,
capturas), no como una declaración de que "ya se hizo".

## 4. Estado técnico verificado hoy (2026-09-13)

Todo lo siguiente se ejecutó realmente en esta sesión, no se copió de un informe
anterior.

### Backend (`apps/api`, Python 3.14, `uv`/venv local)

| Comprobación | Resultado |
| --- | --- |
| `pytest tests/unit` | 267 passed |
| Cobertura (`--cov=app`) | 80,15 % (gate 80 %) |
| `mypy app` | 0 errores (ejecutado antes de un fallo puntual de Windows Defender Application Control que bloqueó una DLL de mypy más tarde en la sesión; es un problema de esta máquina, no del código — repetir en máquina limpia) |
| `ruff check` sobre archivos tocados en 10.1 | limpio |
| `ruff check app tests` (repo completo) | **16 incidencias preexistentes, no tocadas hoy**: 9 en `app/garage/models.py` (`UP042`, `E501` ×6) y `app/files/endpoints.py` (`B008`, `B904` ×2); el resto ya corregido en esta sesión |
| `ruff format --check` (repo completo) | 10 archivos preexistentes sin formatear (`app/connectors/registry.py`, `app/garage/*`, `app/scoring/vocab.py`, `tests/integration/test_watchlist_inspections.py`, `tests/unit/test_vehicles_endpoints.py`) — ninguno tocado hoy |
| Tests de integración (`tests/integration`) | **No ejecutados**: requieren `TEST_DATABASE_URL`/`TEST_REDIS_URL` reales; esta máquina no tiene Docker |
| Migraciones Alembic | Cadena única, `20260913_0010` es `head`, aplicada con éxito en producción |

### Frontend (`apps/web`, pnpm workspace)

| Comprobación | Resultado |
| --- | --- |
| `vitest run` | 121/121 tests |
| Cobertura global | 76,08 % líneas / 67,95 % ramas / 70,53 % funciones — **por debajo del gate (80/75/80)** |
| Causa de la cobertura baja | `features/garage` (7,14 %) y `features/watchlist` (4,76 %) no tienen ni un test desde que se implementaron en Fases 6–7; no es regresión de hoy |
| `tsc --noEmit` | limpio |
| `eslint . --max-warnings=0` | limpio |
| E2E (`playwright test`) | **No ejecutados**: requieren stack completo + navegador, no disponibles en esta sesión |

### Despliegue (Synology NAS, `~/motorscope`)

- Backup de Postgres pre-migración: `~/motorscope_pre_f10_1_backup.dump` (148 KB) en
  el NAS — consérvese hasta confirmar que 10.1 funciona bien en el uso real.
- Migración `20260913_0010` aplicada y verificada (`source_configurations` sembrada
  con `wallapop`/`manual` habilitados).
- Corregido `infrastructure/docker/web.Dockerfile`: la imagen `node:26.8.1-alpine` ya
  no trae `corepack`; se sustituyó por `npm install --global pnpm@11.1.3` (commit
  `8923ccf`). Sin este fix, el build de `web` no compila en ninguna máquina que use
  esa imagen, no solo en el NAS.
- Los 6 contenedores (`caddy`, `web`, `api`, `worker`, `postgres`, `redis`) están
  `healthy`; verificado `GET /` → 200 y `GET /api/v1/health/live` → `{"status":"ok"}`.
- Queda un archivo `motorscope-fixed.tar.gz` (~2,9 MB) tanto en el repo local como en
  el home del NAS, de un intento de despliegue anterior de la sesión de codex; no
  forma parte del código, no se ha comiteado. Se puede borrar sin riesgo.

## 5. Deuda y documentación pendiente de sincronizar

No se ha reescrito por completo (sería un esfuerzo grande y de bajo valor mientras el
proyecto está aparcado); se han dejado señalados como "desactualizado" para que el
siguiente que retome sepa que no son fuente de verdad hasta revisarlos:

- `docs/project_management/planificacion/task.md` — desglose granular por fase
  (F0.x…) solo cubre hasta Fase 5 con detalle; Fases 6–10.1 no tienen su propio
  desglose de sub-tareas.
- `docs/project_management/planificacion/implementation_plan.md` — la tabla de
  progreso y el "punto de relevo" apuntaban a Fase 6 como siguiente paso; ya está
  hecho.
- `docs/architecture/architecture.md` y `docs/domain/data-model.md` — cabeceras
  dicen "implementado hasta Fase 5"; no documentan Watchlist, Inspección, Garage,
  Finance ni Wallapop/búsqueda en vivo.
- No existen `INFORME_CIERRE_FASE_6.md`, `_FASE_7.md`, `_FASE_8.md`, `_FASE_9.md`
  con el nivel de detalle de los de Fases 2–5 (Fase 9 sí existe pero es superficial,
  ver §3).
- **Actualización 2026-09-13 (limpieza final):** `FASE_10_STATUS.md` se borró (su
  contenido ya estaba incorporado y superado por este informe); `PROMPT_FASE_10_1.md`
  se movió a `docs/prompts/PROMPT_FASE_10_1.md` como registro histórico del prompt
  usado. `ESTADO_ACTUAL.md` (raíz del repo) es ahora el punto de entrada único y
  vivo; este informe queda como evidencia detallada de la auditoría de esa fecha.

## 6. Próximos pasos para cuando se retome el proyecto

En orden recomendado:

1. **Decidir sobre Wallapop (§2) antes que nada.** Es la única pieza que tiene
   implicación legal real fuera del propio código. Si se decide seguir, conseguir
   una revisión de términos actualizada o un canal oficial, y actualizar
   `docs/source-compliance.md` para que dicte la verdad. Si se decide parar, basta
   con `enabled: false` en Settings.
2. **Verificar de verdad Fase 8/9** (o aceptar conscientemente que no se va a hacer
   por ahora): ASVS L2, DAST, accesibilidad, restore real. Si se decide que no
   compensa para un proyecto personal/privado, dejarlo escrito explícitamente en vez
   de mantener un informe de cierre que dice lo contrario.
3. **Tests frontend de `garage/` y `watchlist/`**: son las dos áreas que impiden que
   `pnpm test` (web) pase el gate de cobertura. Sin esto, cualquier CI que exija
   cobertura seguirá roja aunque el código funcione.
4. **Limpiar deuda de lint/format preexistente** en `app/garage/models.py`,
   `app/files/endpoints.py` y los 10 archivos sin formatear listados en §4 — es
   mecánico, una tarde como mucho.
5. **Ejecutar los tests de integración y E2E** en una máquina con Docker (o en el
   propio NAS) antes de dar por buena cualquier fase nueva; esta sesión no pudo
   hacerlo por falta de entorno local.
6. **Sincronizar la documentación de planificación** (§5) — o decidir formalmente
   que `task.md`/`implementation_plan.md` quedan congelados y este informe pasa a
   ser la referencia viva mientras el proyecto esté aparcado.
7. Borrar `motorscope-fixed.tar.gz` del repo local y del NAS (artefacto residual, sin
   uso).

## 7. Cómo retomar el entorno técnico (resumen operativo)

- Repo: rama `feature/fase-10-real-search`, al día con `origin`. No se ha mergeado a
  `main` — esa decisión sigue pendiente del propietario.
- NAS: acceso y comandos en `Guia_Conexion_ssh_NAS.md` (raíz del repo). Proyecto en
  `~/motorscope`; backup pre-10.1 en `~/motorscope_pre_f10_1_backup.dump`.
- Backend local: `apps/api`, `uv sync --all-groups`, venv en `.venv`; `pytest`,
  `ruff`, `mypy` documentados en `README.md`. Ejecutar siempre desde `apps/api`, no
  desde la raíz.
- Frontend local: `pnpm install` desde la raíz del monorepo; ejecutar Vitest/ESLint
  siempre desde una unidad mapeada (`Z:`/`N:`), nunca desde la ruta UNC directa,
  porque duplica la ruta y falla.
- Variables/secretos: `.env` vive solo en el NAS y en máquinas de desarrollo, nunca
  en git; ver `.env.example` para las claves requeridas.
