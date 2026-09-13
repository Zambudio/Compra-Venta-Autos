# Estado actual — MotorScope

**⏸️ Proyecto aparcado el 2026-09-13.** Pedro es el único desarrollador y la única
persona que conoce la existencia de este proyecto. No hay presión de tiempo ni
usuarios externos. Este documento es el único punto de entrada necesario para
retomarlo: léelo entero antes de tocar código, documentación o el NAS.

## Instrucciones para la IA que retome esto

1. **No asumas nada de `task.md`, `implementation_plan.md`,
   `docs/architecture/architecture.md` ni `docs/domain/data-model.md`.** Están
   desactualizados desde 2026-09-12 (llevan una etiqueta de aviso en la cabecera).
   Este documento manda sobre ellos.
2. **No te fíes de los "informes de cierre" de fase como prueba de que algo
   funciona.** El de la Fase 9 se autodeclaraba "¡Proyecto Entregado!" y la Fase 10
   tuvo que rehacer la búsqueda porque nunca había funcionado con datos reales.
   Verifica tú mismo (tests, lint, tipos) antes de dar nada por bueno.
3. **Antes de construir nada nuevo sobre el conector Wallapop, decide sobre el
   riesgo legal de la sección 2.** Es una decisión de producto, no técnica; no la
   tomes tú solo/a por inercia.
4. Si el usuario pide "continuar" sin más contexto, empieza preguntando qué
   quiere retomar concretamente (ver "Próximos pasos" más abajo) en vez de asumir
   que hay que seguir el roadmap original punto por punto — el proyecto se aparcó
   precisamente porque ese roadmap se sentía demasiado largo para un proyecto
   personal.
5. El detalle exhaustivo (números exactos de tests/cobertura, historial de
   commits por fase, comandos ejecutados) está en
   [`docs/project_management/informes_cierre/INFORME_ESTADO_Y_RELEVO_2026-09-13.md`](docs/project_management/informes_cierre/INFORME_ESTADO_Y_RELEVO_2026-09-13.md).
   Este documento es el resumen ejecutivo; ese otro es la evidencia.

## 1. Qué hay construido (verificado, no autodeclarado)

Monolito modular: FastAPI + Next.js + PostgreSQL + Redis/Dramatiq + Docker Compose +
Caddy, desplegado en el Synology NAS de Pedro (`~/motorscope`).

| Área | Estado |
| --- | --- |
| Auth, sesiones, CSRF, roles, rate limiting | ✅ |
| Adquisición: conector real de Wallapop + entrada manual | ✅ implementado — ⚠️ riesgo legal, ver §2 |
| Gestión dinámica de fuentes (activar/desactivar, salud, auditoría) | ✅ |
| Búsqueda en vivo con caché y rate limiting | ✅ |
| Normalización, deduplicación, snapshots de anuncios | ✅ |
| Vehículos unificados, matching, histórico, comparables/mercado | ✅ |
| Knowledge Base (evidencias, problemas conocidos, fiabilidad) | ✅ |
| Score de oportunidad versionado (9 componentes) | ✅ |
| Watchlist e Inspección (checklist, adjuntos) | ✅ implementado — sin tests frontend |
| Garage/Finance (compra, ledger, venta, ROI) | ✅ implementado — sin tests frontend |
| Hardening (ASVS L2, DAST, accesibilidad, restore real) | ⚠️ autodeclarado en su día, sin evidencia real |

Última migración aplicada en producción: `20260913_0010`. Rama de trabajo
`feature/fase-10-real-search`, ya mergeada en `main`.

## 2. Riesgo abierto: conector Wallapop

`apps/api/app/connectors/wallapop.py` llama a una API privada/no oficial de
Wallapop (`api.wallapop.com/api/v3/cars/search`) simulando ser un navegador
(`User-Agent` falso). El propio `docs/source-compliance.md` del proyecto —
escrito en la Fase 0 — dice que los términos de Wallapop prohíben esto
explícitamente, y que haría falta una revisión legal real antes de automatizarlo.
Esa revisión nunca se hizo; una migración de la Fase 10 se "autoaprobó" a sí misma
sin respaldo real.

**Decisión tomada el 2026-09-13:** se deja el conector activo en producción tal
cual, porque Pedro es el único que conoce y usa la plataforma y no hay exposición
a terceros mientras esté así. Si esto cambia — se comparte acceso, se hace público,
se aumenta el volumen de uso, o se retoma desarrollo activo — hay que resolver este
punto antes de seguir: conseguir un canal oficial/autorización real, o desactivar
el conector (`PATCH /sources/wallapop/config {"enabled": false}`, o el toggle en
Settings — reversible al instante, sin redeploy).

No hay ningún job en segundo plano que llame a Wallapop solo; solo se activa si
alguien busca en vivo o fuerza una sincronización desde la web.

## 3. Deuda conocida (no bloqueante para dejarlo aparcado)

- Cobertura frontend por debajo del gate (76% vs 80%) porque `garage/` y
  `watchlist/` no tienen ningún test desde que se implementaron.
- Lint/format pendiente en `app/garage/models.py` y `app/files/endpoints.py`
  (preexistente, no relacionado con el trabajo de esta semana).
- Tests de integración y E2E no se han podido ejecutar desde la máquina de
  desarrollo Windows (falta Docker/Postgres/Redis local).
- Documentación de planificación (`task.md`, `implementation_plan.md`,
  `docs/architecture/`, `docs/domain/data-model.md`) desincronizada desde
  2026-09-12; marcada con avisos pero no reescrita.

## 4. Próximos pasos, si se retoma

No hay orden obligatorio — elegir según lo que apetezca hacer al volver:

1. Resolver el riesgo de Wallapop (§2) si se va a seguir usando la búsqueda real.
2. Tests frontend de `garage/` y `watchlist/` para que el gate de cobertura pase.
3. Verificar de verdad Fase 8/9 (ASVS, DAST, accesibilidad, restore) o aceptar
   explícitamente que no se va a hacer para un proyecto personal.
4. Limpiar la deuda de lint/format preexistente (mecánico, corto).
5. Ejecutar integración/E2E en una máquina con Docker antes de dar por buena
   cualquier fase nueva.
6. Sincronizar `task.md`/`implementation_plan.md`/`architecture.md`/
   `data-model.md`, o decidir formalmente que quedan congelados y este documento
   pasa a ser la única fuente de verdad viva.

## 5. Acceso y comandos

- NAS: `docs/operations/Guia_Conexion_ssh_NAS.md` (conexión, Docker, despliegue).
- Backend local (`apps/api`): `uv sync --all-groups`, luego `ruff format --check .`,
  `ruff check .`, `mypy app tests`, `pytest -m "not integration" -p no:cacheprovider`.
- Frontend local (`apps/web`, monorepo pnpm): `pnpm install --frozen-lockfile`,
  luego `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`. En Windows,
  ejecutar siempre desde una unidad mapeada (`Z:`/`N:`), nunca desde la ruta UNC
  directa.
- Backup de base de datos previo al último despliegue:
  `~/motorscope_pre_f10_1_backup.dump` en el NAS.
