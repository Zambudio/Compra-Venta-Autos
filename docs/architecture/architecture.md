# Arquitectura

Estado: inicial, aprobado para Foundation. Fecha: 2026-09-06.

## Contexto y restricciones

MotorScope es una herramienta privada de bajo volumen cuyo valor depende de datos trazables y cálculos correctos. Se adopta un monolito modular: un despliegue backend, una base PostgreSQL y módulos de dominio con límites explícitos. Redis y procesos separados soportan jobs, pero no crean microservicios.

## Vista de contenedores

```text
Navegador
   │ HTTPS
   ▼
Caddy ─────► Next.js web
   └───────► FastAPI /api/v1
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
     PostgreSQL          Redis/Dramatiq
                              │
                              ▼
                         Worker FastAPI package
```

Solo Caddy publica puertos. PostgreSQL y Redis viven en una red interna. API y worker comparten el mismo paquete y modelo de dominio.

## Monorepo

```text
apps/api/app/
  core/ auth/ users/ vehicles/ listings/ search/ connectors/
  knowledge/ scoring/ opportunities/ watchlist/ inspections/
  garage/ finance/ notifications/ files/ audit/
apps/web/
packages/shared/
infrastructure/docker/ infrastructure/caddy/ infrastructure/scripts/
docs/ tests/
```

Fase 1 implementó `core`, `auth`, `users` y `audit`. Fase 2 implementa
`connectors`, `listings`, `sources` y `search`; el resto de directorios son
límites declarados sin lógica de negocio hasta su fase.

## Regla de dependencia

- `api` traduce HTTP a DTOs y llama casos de uso.
- `application` coordina transacciones y puertos.
- `domain` conserva reglas y tipos sin depender de FastAPI/SQLAlchemy.
- `infrastructure` implementa persistencia, Redis, reloj, hashes o fuentes externas.
- Un dominio no importa infraestructura interna de otro. La comunicación síncrona usa servicios públicos explícitos; la asíncrona usa mensajes versionados cuando sea necesario.
- El patrón Repository se añade solo cuando desacopla una regla de dominio o facilita una prueba; no se crean wrappers CRUD vacíos.

## Módulos y responsabilidades

| Módulo                     | Responsabilidad                                          | Fase        |
| -------------------------- | -------------------------------------------------------- | ----------- |
| core                       | configuración, DB, Redis, errores, observabilidad, broker | 1 / 2      |
| auth/users/audit           | identidad, sesiones, roles y eventos auditables          | 1           |
| search/connectors/listings/sources | filtros, adquisición permitida, normalización, ingesta, snapshots, health | 2 |
| vehicles                   | identidad normalizada y deduplicación                    | 3           |
| knowledge                  | jerarquía técnica, problemas, fuentes y evidencias       | 4           |
| scoring/opportunities      | perfiles, score y valoración explicable                  | 5           |
| watchlist/inspections      | seguimiento y checklists                                 | 6           |
| garage/finance             | propiedad, ledger, venta y ROI                           | 7           |
| notifications/files        | puertos reemplazables de entrega/almacenamiento          | transversal |

## Contratos externos

La adquisición sigue `Search Engine → Connector → Provider → Normalizer`. Un `Connector` conoce semántica de una fuente; un `Provider` conoce el medio autorizado; el `Normalizer` produce DTO interno. Fase 2 implementa `MockConnector` (catálogo determinista versionado, con latencia y fallos transitorios simulados) y `ManualEntryConnector` (ficha aportada bajo acción humana); el registro (`app/connectors/registry.py`) solo expone estos dos. Ningún conector de portal real está activo. La ingesta (`ListingService.ingest_raw`) es idempotente: dedup por `payload_hash` + `(source_id, external_id)`, `RawListingPayload` inmutable, `ListingSnapshot` solo ante cambio real. Las sincronizaciones se ejecutan síncronas o mediante el actor Dramatiq `sync_source_actor` (idempotente por `run_id`).

## Datos y consistencia

PostgreSQL es la fuente de verdad. Dinero usa `Numeric/Decimal` con moneda explícita; tiempos se almacenan en UTC; constraints reales protegen invariantes. Las operaciones de negocio se ejecutan en transacciones. Alembic es la única vía de esquema.

Redis solo almacena estado efímero: colas, rate limits, locks y deduplicación temporal. Perder Redis no debe perder datos de negocio. Jobs son idempotentes, con timeout, backoff, máximo de intentos, `job_id` y registro de fallo.

## API y frontend

La API se versiona en `/api/v1`, usa request/response separados y errores uniformes. No expone modelos ORM ni `raw_data`. Next.js usa Server Components por defecto; los formularios interactivos son Client Components. Las reglas críticas permanecen en backend.

## Observabilidad

Cada petición recibe/valida `X-Request-ID`, se registra en JSON y se devuelve al cliente. Hay liveness, readiness de PostgreSQL/Redis y métricas Prometheus. Los logs no contienen credenciales, cookies, tokens ni payloads personales. La estructura deja un punto de extensión para OpenTelemetry sin imponerlo en Foundation.

## Calidad y seguridad

Los gates están en `docs/testing/testing-strategy.md` y `docs/security/asvs.md`. La autenticación y autorización son dependencias explícitas, no visibilidad de UI. CORS se limita a orígenes configurados; Caddy termina TLS en remoto. Véanse ADRs 0001–0011.

## Restricciones conscientes

No se introduce microservicios, CQRS, event sourcing, Kafka, Kubernetes, ML ni vector DB. Cualquier cambio requiere evidencia y ADR antes de implementación.
