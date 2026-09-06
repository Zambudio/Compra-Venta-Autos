# Modelo de dominio y datos

Estado: modelo lógico del MVP. Fase 1 implementó identidad, sesión y auditoría;
Fase 2 implementa fuentes y anuncios (`sources`, `source_compliance_reviews`,
`source_sync_runs`, `vehicle_listings`, `raw_listing_payloads`, `listing_snapshots`).
Fecha: 2026-09-06.

## Principios

- `Vehicle` y `Listing` son identidades distintas y obligatorias.
- IDs internos estables (UUID); IDs externos tienen unicidad por fuente.
- Timestamps UTC; dinero `Numeric/Decimal` y código ISO 4217.
- Constraints e índices responden a invariantes/consultas reales.
- Los DTOs API nunca son modelos ORM.
- Soft delete solo si una obligación de trazabilidad lo exige.

## Relaciones principales

```text
User 1─* Session             User 1─* AuditEvent
Source 1─* SourceComplianceReview
Search 1─1 SearchFilter      Search *─* Source
Vehicle 1─* Listing          Listing 1─* ListingSnapshot
Vehicle 1─* VehicleMatchCandidate *─1 Vehicle (candidato)

Manufacturer 1─* Model 1─* Generation 1─* Engine 1─* EngineVariant
Transmission *─* Generation/EngineVariant
KnowledgeSource 1─* Evidence *─1 KnownIssue
VehicleClassification → Model|Generation|Engine|EngineVariant|Transmission|Combination

ScoringProfile 1─* ScoringProfileVersion 1─* OpportunityScore
Vehicle/Listing 1─* MarketEstimate
Opportunity → Vehicle + Listing + OpportunityScore + MarketEstimate
Vehicle 1─* WatchlistEntry   Vehicle 1─* Inspection 1─* InspectionItem
Opportunity 0..1─1 OwnedVehicle 1─* Expense 0..1─1 Sale
FileAttachment → entidad autorizada
Notification → User + evento
```

## Entidades de Foundation

### User

`id`, `email` normalizado, `password_hash`, `role` (`OWNER|ADMIN|VIEWER`), `is_active`, `created_at`, `updated_at`, `password_changed_at`. Email único case-insensitive. Nunca se devuelve `password_hash`.

### Session

`id`, `user_id`, `token_hash` único, `csrf_token_hash`, `created_at`, `expires_at`, `last_seen_at`, `revoked_at`, metadatos mínimos de cliente opcionales. El token bruto no se almacena. Borrar/revocar sesiones expiradas mediante tarea operativa.

### AuditEvent

`id`, `actor_user_id` nullable, `action`, `entity_type`, `entity_id`, `occurred_at`, `request_id`, `result`, `metadata` JSONB saneado. No contiene secretos ni payloads personales completos.

## Entidades de adquisición y mercado

**Implementadas en Fase 2** (ver [ADR-0012](../adr/0012-listing-ingestion-and-dedup.md)):

- `Source` (`sources`): `key` único (`mock`, `manual`), `name`, `provider_kind`
  (`MOCK|MANUAL|CONNECTOR`), `is_active`, `is_automatable`, timestamps.
- `SourceComplianceReview` (`source_compliance_reviews`): `acquisition_method`,
  `automated_allowed`, `authentication_required`, `rate_limit`, `terms_url`,
  `checked_at`, `notes`. Append-only; se siembra por migración de datos `20260906_0003`.
- `SourceSyncRun` (`source_sync_runs`): `status` (`PENDING|RUNNING|SUCCESS|PARTIAL|FAILED`),
  `mode`, `filters` JSONB saneado, `request_id`, contadores (`listings_seen/created/updated`,
  `snapshots_created`), `error_summary` sin trazas, `started_at`/`finished_at`.
- `VehicleListing` (`vehicle_listings`): anuncio por `(source_id, external_id)` (único).
  Campos normalizados del Plan Maestro §11; dinero `Numeric(12,2)` + moneda; enums
  con CHECK; `entry_channel` (`MOCK_SYNC|MANUAL_ENTRY`); `payload_hash` del último
  payload; `first_seen_at`, `last_seen_at`, `published_at`. Índices por
  `(brand, model)`, `price_amount`, `year`, `last_seen_at`, `status`.
- `RawListingPayload` (`raw_listing_payloads`): payload original **inmutable** (JSONB),
  `payload_hash`, `connector_version`, `retrieved_at`. Único `(source_id, payload_hash)`.
  Nunca se expone por API.
- `ListingSnapshot` (`listing_snapshots`): observación append-only con precio, moneda,
  km, estado y `description_hash`. Se añade solo cuando cambia precio, km o descripción.

**Pendientes (Fase 3+):**

- `Vehicle`: vehículo normalizado independiente de sus anuncios. `VehicleListing.vehicle_id`
  se añadirá como columna nullable; la asociación es tardía y no destructiva.
- `VehicleMatchCandidate`: par de vehículos/listings, confianza, razones y decisión manual.
- `MarketEstimate`: intervalo, método, cantidad de comparables, confianza y fecha.
- `Search` / `SearchFilter` persistidos: la Fase 2 usa `SearchFilter` tipado en memoria
  (`app/search/schemas.py`) y registra las sincronizaciones en `SourceSyncRun`.

`VehicleListing` existe sin `Vehicle`; la deduplicación de Fase 2 es solo
`payload_hash` + `(source_id, external_id)`. La deduplicación entre fuentes por
señales del anuncio nunca colapsa por una única señal (Fase 3).

## Knowledge Base

- Jerarquía: `Manufacturer → Model → Generation → Engine → EngineVariant`; `Transmission` es independiente y relacionable.
- `KnowledgeSource`: tipo, nombre, URL, publisher, fechas y nivel A–D.
- `Evidence`: componente, problema, resumen/cita limitada, severidad, confianza y verificación.
- `KnownIssue`: afirmación técnica con estado `DRAFT|REVIEWED|VERIFIED|DEPRECATED`; no existe como verificada sin evidencia suficiente.
- `VehicleClassification`: `WHITELIST|WATCHLIST|BLACKLIST|UNKNOWN` sobre un objetivo tipado, con vigencia y evidencias.

Las mitigaciones de una unidad se vinculan a `Vehicle`/`Inspection`; nunca reescriben la reputación general.

## Scoring y oportunidades

- `ScoringProfile` agrupa versiones.
- `ScoringProfileVersion` es inmutable y almacena pesos/configuración, suma validada y vigencia.
- `OpportunityScore` persiste total, nueve componentes, explicación, instante y versión.
- `Opportunity` referencia la unidad y la observación base; conserva valores económicos como estimaciones con intervalo/confianza, no certezas.
- `WatchlistEntry` tiene estado controlado y precio al guardar.

## Inspección, propiedad y finanzas

- `Inspection` / `InspectionItem`: checks genéricos/específicos con `PASS|WARNING|FAIL|NOT_CHECKED`, notas y adjuntos.
- `OwnedVehicle`: nace de una oportunidad y conserva todo el histórico previo.
- `Expense`: ledger append/correcciones auditadas; importe, impuesto y moneda `Numeric`, categoría controlada.
- `Sale`: precio/fecha/km y gastos de venta. Beneficio/ROI se calculan desde compra + ledger + venta.

## Servicios transversales

- `FileAttachment`: nombre interno aleatorio, nombre original saneado, MIME detectado, tamaño, hash, storage key, propietario/entidad y fechas.
- `Notification`: canal, evento, idempotency key, estado e intentos.
- `AuditEvent`: registro de seguridad y cambios relevantes.

## Índices y concurrencia previstos

Índices mínimos: email normalizado, hash de sesión, expiración de sesión, `(source, external_id)`, snapshots por `(listing_id, observed_at)`, listings por vehicle/estado/precio/fecha, evidencia por issue/source, scores por opportunity/version. Se añadirán índices adicionales solo con consultas/planes medidos. `version` de locking optimista se añadirá a agregados con edición concurrente demostrada.

## Retención

Sesiones expiradas: purga operativa tras la ventana de auditoría. Raw payloads, matrículas, teléfonos, ubicaciones precisas y documentos requieren base/finalidad, retención y acceso definidos antes de Fase 2/7. Los eventos de auditoría se conservan según política de seguridad, con metadatos minimizados.
