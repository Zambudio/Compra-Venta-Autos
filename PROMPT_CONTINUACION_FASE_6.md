# Prompt de continuación — MotorScope, baseline y Fase 6

Copia desde la línea siguiente y entrégalo al siguiente agente.

---

Continúa el desarrollo de MotorScope de forma autónoma en el repositorio
`N:\IA\02_Proyectos\Compra-Venta Autos` (UNC equivalente:
`\\zambu-nas\nas-drive-pedro\IA\02_Proyectos\Compra-Venta Autos`). Responde en
español. No hagas preguntas salvo que exista una decisión irreversible o falte una
credencial imprescindible. Tienes autorización para editar, ejecutar pruebas, usar
Docker/SSH según los runbooks, crear commits y hacer push cuando todos los gates estén
verdes.

## Objetivo único

Recupera primero el baseline de calidad (`F6.0`) y después implementa completa la
**Fase 6 — Watchlist e Inspección**. No empieces Fase 7. Cierra con migración,
documentación, CI/Security verdes, despliegue y smoke test en el Synology NAS.

## Fuentes de verdad, en este orden

1. Lee completo `PLAN_MAESTRO_VEHICULOS_SEGUNDA_MANO.md`; para esta fase son críticos
   §§22, 24, 34, 42–45, 53–58.
2. Lee `task.md`; F6.0–F6.6 contienen el desglose y los criterios de aceptación.
3. Lee `implementation_plan.md` y
   `INFORME_ESTADO_Y_RELEVO_2026-09-12.md`.
4. Lee ADR-0014 (Knowledge Base), ADR-0015 (scoring), arquitectura, data flow, modelo
   de datos, threat model, ASVS, testing, deployment y backup/restore.
5. Usa `INFORME_CIERRE_FASE_5.md` como evidencia histórica, no como estado actual.

## Estado exacto de partida

- Rama `main`; `HEAD` y `origin/main`: `3e93e3c`.
- Fases 0–5 implementadas. Última migración:
  `20260909_0006_scoring_and_opportunities.py`.
- Fase 5 desplegada en NAS `192.168.1.3:3080`, migración `0006`, smoke 9/9 y 6
  contenedores saludables según el informe de cierre.
- Backend actual: 254/254 unit tests; cobertura 85,42%.
- Frontend actual: 109/109 tests; TypeScript pasa; ramas 72,81% y el gate exige 75%.
- CI actual falla en `ruff format --check` y `pnpm format:check`; E2E no se ejecuta.
- Deuda local: Ruff 17 incidencias/4 archivos; mypy 13 errores/7 archivos; ESLint
  1 error + 13 warnings; Prettier 25 archivos.
- Security: SAST, secret/dependency scans y CodeQL pasan; Trivy falla para imagen web.
- Hay tres archivos no versionados en `apps/web/public/brand/`. Presérvalos; no los
  borres ni los incluyas en commits hasta revisar origen/licencia y uso previsto.

## Paso 1 obligatorio — F6.0

Antes de añadir modelos o endpoints:

1. Crea una rama `feature/fase-6-watchlist-inspections` desde `main` actualizado.
2. Corrige formato, imports y lint backend/frontend.
3. Resuelve mypy sin desactivar strict ni añadir ignores amplios.
4. Corrige `react-hooks/set-state-in-effect` con un patrón de carga idiomático; no
   suprimas la regla.
5. Añade pruebas útiles de oportunidades hasta superar 75% de ramas globales.
6. Revisa el fallo Trivy de la imagen web. Corrige dependencias/base si hay fix; si no,
   solo usa `.trivyignore` con CVE exacto, justificación, compensación, responsable y
   caducidad.
7. Regenera OpenAPI y valida que no haya un diff accidental.
8. Haz commit del saneamiento separado del desarrollo funcional. Push y confirma CI
   y Security completos, incluido E2E. Si el baseline no queda verde, no avances.

Comandos canónicos en Windows:

```powershell
cd "N:\IA\02_Proyectos\Compra-Venta Autos\apps\api"
uv run ruff format --check .
uv run ruff check .
uv run mypy app tests
uv run pytest -m "not integration" -p no:cacheprovider

cd "N:\IA\02_Proyectos\Compra-Venta Autos\apps\web"
.\node_modules\.bin\prettier.cmd --check .
.\node_modules\.bin\eslint.cmd . --max-warnings=0
.\node_modules\.bin\tsc.cmd --noEmit
.\node_modules\.bin\vitest.cmd run --coverage
.\node_modules\.bin\next.cmd build --webpack
```

No ejecutes Vitest desde el UNC: en este host duplica la raíz. Usa `N:` o `Z:`. Para
pytest, trabaja desde `apps/api`; `uv run --project` desde la raíz no carga aquí la
configuración de pytest correctamente.

## Diseño obligatorio — ADR-0016 antes de la migración

Registra al menos:

- `WatchlistEntry` ligado a `Opportunity`, con referencias estables a listing/vehicle;
- estados `WATCHING|CONTACTED|VISIT_PLANNED|INSPECTED|REJECTED|PURCHASED` y matriz de
  transiciones explícita;
- precio al guardar persistido; precio actual/histórico derivados de
  `ListingSnapshot`, sin duplicar series;
- `Inspection` y `InspectionItem`; checklist congelado al crear la inspección;
- checks genéricos del Plan Maestro + específicos derivados de `KnownIssue` para
  modelo/generación/motor/cambio, conservando referencia a evidencia;
- resultados `PASS|WARNING|FAIL|NOT_CHECKED`, notas y auditoría;
- `FileAttachment` y puerto `FileStorage`; almacenamiento local fuera de webroot,
  migrable a S3 en V2;
- RBAC/CSRF, ownership, retención, backup y eliminación controlada.

No guardes binarios en PostgreSQL. No calcules checks con LLM. No permitas que una
edición posterior de Knowledge Base altere retroactivamente una inspección existente.

## Implementación esperada

### Backend y persistencia

- Módulos `app/watchlist`, `app/inspections` y `app/files` respetando los límites del
  monolito modular.
- Migración Alembic `0007`, reversible y probada desde `0006` y sobre base vacía.
- DTOs separados del ORM, errores RFC 7807, endpoints bajo `/api/v1`.
- Operaciones de mutación con rol, CSRF, transacción y `AuditEvent`.
- Subida segura: nombre aleatorio, MIME por contenido, allowlist, límite, hash,
  storage key opaco, prevención de ejecución y descarga autorizada.
- OpenAPI regenerado.

### Frontend

- Acción para guardar una oportunidad y pestaña/vista Watchlist.
- Precio guardado, actual, variación e histórico; notas y estados.
- Flujo de visita e inspección, checklist por secciones y progreso visible.
- Fotos con feedback de validación/subida.
- Estados loading/error/empty/success, mobile-first, teclado completo, foco visible y
  cero violaciones `vitest-axe`.
- Mantén la dirección visual actual de MotorScope; reutiliza componentes y tokens.

### Pruebas

- TDD para reglas de transición y generación de checklist.
- Unit tests de dominio y servicios; integración PostgreSQL real para constraints,
  migración, transacciones y autorización.
- Tests negativos de archivos: MIME falso, extensión engañosa, tamaño, path traversal,
  acceso de otro usuario/rol y contenido corrupto.
- Component tests + axe y Playwright del flujo oportunidad → watchlist → inspección.
- Smoke NAS reproducible que valide health, login, watchlist, cambio de precio,
  inspección, adjunto y decisión final.

## Restricciones permanentes

- Cero scraping de portales reales; solo Mock/Manual.
- Cero ML o LLM decisor. Todo cálculo debe ser determinista, explicable y auditable.
- Dinero siempre `Decimal/Numeric` y moneda explícita.
- No S3, correo/push, Garage/Finance ni otras capacidades de Fase 7+.
- No marques `[x]` si algún criterio, test o gate está pendiente.
- No ocultes deuda con skips, umbrales menores, reglas desactivadas o ignores amplios.
- Preserva cambios ajenos y archivos no versionados.

## Cierre requerido

1. Actualiza `task.md`, `implementation_plan.md`, arquitectura, data flow, data model,
   threat model, ASVS, testing, deployment, backup/restore y README donde aplique.
2. Genera `INFORME_CIERRE_FASE_6.md` con comandos, métricas y evidencias reales.
3. Aplica `0007` en el NAS, reconstruye servicios afectados y ejecuta el smoke.
4. Commit y push por bloques revisables; confirma CI y Security verdes.
5. Informa archivos cambiados, migración, endpoints, tests/cobertura, estado CI,
   despliegue y riesgos residuales.
6. Detente. No inicies Fase 7.

Empieza inspeccionando `git status`, `git log`, los workflows y los archivos señalados
por los gates. Después ejecuta F6.0; no reescribas desde cero lo que ya funciona.
