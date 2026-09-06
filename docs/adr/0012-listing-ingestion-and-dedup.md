# ADR-0012: Ingesta de anuncios y deduplicación en Fase 2

- **Estado:** Aceptado
- **Fecha:** 2026-09-06

## Contexto

La Fase 2 introduce adquisición de anuncios mediante `MockConnector` y
`ManualEntryConnector` (ADR-0006). Hace falta decidir cómo se persiste lo observado,
cómo se evita duplicar y cómo se conserva trazabilidad, sin adelantar la entidad
`Vehicle` ni la deduplicación entre portales, que corresponden a Fase 3 (ADR-0005).

## Decisión

- `VehicleListing` es la unidad persistida de Fase 2: un anuncio por
  `(source_id, external_id)` con restricción única. No se crea `Vehicle` todavía;
  `VehicleListing.vehicle_id` se añadirá en Fase 3.
- `RawListingPayload` almacena el payload original inmutable (JSONB) con
  `payload_hash = sha256(canonical_json(payload))` y restricción única
  `(source_id, payload_hash)`. Nunca se actualiza ni se expone por API.
- Deduplicación de Fase 2 = identidad de fuente `(source_id, external_id)` + hash de
  payload. Un payload ya visto solo refresca `last_seen_at`. Un payload nuevo para un
  `external_id` conocido actualiza el listing y añade `ListingSnapshot` si cambió
  precio, kilometraje, estado o hash de descripción.
- `ListingSnapshot` es append-only y da el histórico del Plan Maestro §12.
- `SourceSyncRun` registra cada sincronización (estado, contadores, error saneado)
  para observabilidad de jobs (§39/§41) y idempotencia del actor Dramatiq por `run_id`.
- Las filas fijas de `Source` y `SourceComplianceReview` (`mock`, `manual`) se siembran
  en una migración de datos separada de la de esquema (§38).

## Alternativas

- Fusionar anuncios en un `Vehicle` desde Fase 2: prematuro y contrario a ADR-0005.
- No guardar el payload original: impide depurar el normalizador y rompe trazabilidad.
- Deduplicar por señales del anuncio (matrícula, teléfono, fotos): es trabajo de
  Fase 3 con `VehicleMatchCandidate` y revisión humana.
- Sobrescribir el listing sin snapshots: pierde precio inicial, bajadas y días en mercado.

## Consecuencias

Ingesta idempotente y trazable con esquema mínimo. El histórico de precio queda
disponible desde el primer día. La asociación a `Vehicle` y la deduplicación entre
fuentes se incorporan en Fase 3 sin migrar datos destructivamente (solo se añade
`vehicle_id` nullable y el workflow de matching). Los DTOs de API nunca devuelven
`payload` ni `payload_hash`.
