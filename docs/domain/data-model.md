# Modelo de dominio y datos

Estado: modelo lógico del MVP; Foundation implementa únicamente identidad, sesión y auditoría. Fecha: 2026-09-06.

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

- `Source`: catálogo de portales/importadores y estado.
- `SourceComplianceReview`: método, permitido, auth, rate limit, términos, fecha y notas; historial, no simple sobrescritura.
- `Search` / `SearchFilter`: ejecución y filtros tipados del Plan Maestro.
- `Listing`: anuncio por `(source_id, external_id)`, URL y campos observados normalizados.
- `ListingSnapshot`: observación append-only con precio, km, estado y hash de descripción.
- `Vehicle`: vehículo normalizado independiente de sus anuncios.
- `VehicleMatchCandidate`: par de vehículos/listings, confianza, razones y decisión manual.
- `MarketEstimate`: intervalo, método, cantidad de comparables, confianza y fecha.

`Listing` puede existir antes de enlazarse a un `Vehicle`; varios listings pueden apuntar al mismo vehículo. Nunca se colapsan por una única señal.

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
