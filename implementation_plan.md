# Plan de implementación

Última actualización: 2026-09-06. El estado ejecutable vive en `task.md`; este documento describe el orden y los gates.

## Resultado de la inspección

El directorio contenía únicamente `PLAN_MAESTRO_VEHICULOS_SEGUNDA_MANO.md` (47.119 bytes). No era un repositorio Git y no había código, dependencias, configuración, secretos, artefactos compilados ni instrucciones locales adicionales. Por tanto:

- no existe código reutilizable ni deuda de compatibilidad;
- la estructura propuesta por el Plan Maestro puede adoptarse sin adaptación;
- Git se inicializa como parte de Foundation, sin crear remoto ni publicar contenido;
- Docker no está instalado en la máquina de trabajo; los gates que exigen contenedores deberán ejecutarse en CI o en un host con Docker antes de declarar Fase 1 completa.

## Alcance confirmado del MVP

Producto privado, inicialmente para un único `OWNER`, orientado a pocas operaciones anuales y un vehículo simultáneo. El vertical slice prioritario es: login → búsqueda → resultados normalizados → wiki técnica → score explicable → watchlist → compra → gastos → venta → beneficio y ROI.

Quedan fuera del MVP: scraping no autorizado, ML, agentes LLM decisores, microservicios, Kubernetes, Kafka, event sourcing, CQRS complejo y bases vectoriales. Fase 1 no implementa ninguna función de vehículos; solo la plataforma segura que las soportará.

## Orden obligatorio

| Fase   | Entrega                                                                              | Gate de salida                                                                |
| ------ | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| 0 ✅   | Inspección, alcance, documentación, riesgos y ADRs                                   | Completada.                                                                   |
| 1 ✅   | Monorepo, entorno, persistencia, observabilidad, CI, seguridad y auth                | Completada; informe de cierre de Foundation emitido.                          |
| 2 ✅   | Search, contratos de adquisición, conectores mock/manual, normalización, ingesta idempotente y snapshots | Completada 2026-09-06; `INFORME_CIERRE_FASE_2.md`. Conectores, compliance (ADR-0012), pruebas sin portales reales, despliegue y smoke test en el NAS. |
| 3      | Vehicle/Listing, deduplicación, comparables e histórico                              | PostgreSQL real, decisiones manuales para matches inciertos                   |
| 4    | Knowledge Base, evidencias y clasificación                                           | Ninguna afirmación mecánica sin fuente trazable                               |
| 5    | Scoring, valoración y oportunidades                                                  | Score determinista, versionado, explicable y cubierto                         |
| 6    | Watchlist e inspección                                                               | Estados y checklists verificados                                              |
| 7    | Garage, ledger, venta y ROI                                                          | Flujo financiero completo con `Decimal/Numeric`                               |
| 8    | Hardening ASVS L2, DAST, rendimiento, accesibilidad y restore                        | Sin HIGH/CRITICAL abiertos; restore probado                                   |
| 9    | Release MVP                                                                          | Release, migración, rollback y smoke tests reproducibles                      |

## Foundation: diseño técnico

- **Backend:** monolito modular FastAPI bajo `/api/v1`; límites por dominio y dependencias explícitas.
- **Persistencia:** PostgreSQL como única fuente persistente. SQLAlchemy async + psycopg; Alembic es la única vía de esquema.
- **Jobs:** Dramatiq con Redis. Los actores de negocio comienzan en Fase 2; Foundation entrega broker y worker saludable.
- **Frontend:** Next.js App Router, Server Components por defecto y cliente solo donde hay interacción. TanStack Query para estado remoto; React Hook Form + Zod para formularios.
- **Autenticación:** sesiones opacas de alta entropía persistidas como hash SHA-256, contraseñas Argon2id, CSRF sincronizado, roles explícitos y denegación por defecto.
- **Operación:** Docker Compose con Caddy; PostgreSQL y Redis solo en red interna. Logs JSON, request ID, métricas, liveness y readiness.
- **Tooling:** `uv` para Python y workspace `pnpm` para TypeScript; lockfiles obligatorios.

## Estrategia de entrega y pruebas

Cada slice sigue red → verde → refactor. Unit tests no requieren infraestructura; integración y migraciones usan PostgreSQL real, y los tests que validan Redis usan Redis real. La suite normal nunca llama portales externos. CI separa checks rápidos, integración, E2E y seguridad.

No se declara una fase completa si falla: formato, lint, tipos, unit, integración aplicable, frontend, E2E aplicable, migraciones, seguridad o documentación. Un check no ejecutado no equivale a aprobado.

## Riesgos y mitigaciones

| ID   | Riesgo                                       | Impacto                              | Mitigación / estado                                                                    | Responsable                       |
| ---- | -------------------------------------------- | ------------------------------------ | -------------------------------------------------------------------------------------- | --------------------------------- |
| R-01 | Condiciones de portales impiden scraping     | Alto/legal y continuidad             | Solo importación manual/mock hasta autorización; revisión previa por fuente            | Product Owner + responsable legal |
| R-02 | Docker no disponible en el host actual       | Alto para pruebas integradas y build | CI con servicios reales; ejecutar también localmente al instalar Docker                | Tech Lead                         |
| R-03 | Datos personales de vendedores/matrículas    | Alto/privacidad                      | Minimización, retención, cifrado, acceso y auditoría; diseño detallado antes de Fase 2 | Security Owner                    |
| R-04 | Datos mecánicos o de mercado incorrectos     | Alto/decisión de compra              | Evidencias obligatorias, confianza, comparables y revisión humana                      | Domain Owner                      |
| R-05 | Dependencias de versiones muy recientes      | Medio/compatibilidad                 | Versiones estables fijadas, lockfiles, CI y Renovate/Dependabot                        | Tech Lead                         |
| R-06 | Copias de seguridad no restauradas aún       | Alto/operación                       | Runbook definido; prueba real obligatoria en Fase 8 antes de release                   | Operations Owner                  |
| R-07 | Aplicación privada expuesta por error        | Alto/seguridad                       | Auth por defecto, Caddy/TLS, firewall, DB/Redis internos, ASVS L2                      | Security Owner                    |
| R-08 | El filesystem UNC no admite symlinks de pnpm | Bajo/tooling local                   | `node-linker=hoisted`, pins exactos y strict peers; decisión registrada en ADR-0011    | Tech Lead                         |

## Decisiones pendientes

No hay una decisión pendiente que bloquee Foundation. Antes de producción deberán decidirse y documentarse: proveedor/host de secretos, dominio, VPS/plataforma, correo de recuperación (si se incorpora), responsable nominal de backups y base jurídica/retención definitiva de cada dato personal. Ninguna de ellas se presupone en el código.

## Regla de parada

El informe de la sección 60 se emitió al cerrar Fase 1. El usuario autorizó Fase 2 el
2026-09-06; su alcance y decisiones están en `task.md` (F2.1–F2.10), [ADR-0012](docs/adr/0012-listing-ingestion-and-dedup.md)
y ADR-0006. Fase 3 vuelve a requerir aprobación explícita: no se inicia sin ella.
