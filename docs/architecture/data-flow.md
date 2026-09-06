# Flujos de datos

Estado: diseño inicial. Fecha: 2026-09-06.

## Acceso en Foundation

```text
Usuario → Caddy → Next.js → POST /api/v1/auth/login
                              │ valida DTO + rate limit
                              ▼
                         PostgreSQL User
                              │ Argon2id
                              ▼
                    Session(token_hash, csrf_hash, expiry)
                              │
             Set-Cookie session HttpOnly + csrf no HttpOnly
                              ▼
                    GET /api/v1/auth/me
```

El token opaco y el CSRF nacen de CSPRNG. Solo sus hashes se persisten. El logout exige sesión + token CSRF y revoca la fila. Login/logout/fallos generan `AuditEvent` saneado con `request_id`.

## Petición autenticada

```text
Cookie sesión → hash → Session vigente/no revocada → User activo → rol requerido
Mutación       → cookie CSRF + X-CSRF-Token → comparación constante + hash persistido
```

Cualquier fallo termina en 401/403 uniforme; no se confía en el frontend.

## Adquisición implementada (Fase 2)

```text
SearchFilter / SyncRequest validado (Pydantic)
  → SourceService.create_run  →  SourceSyncRun(PENDING)
      → mode=sync: execute_run en la petición
      → mode=async: sync_source_actor.send(source_key, run_id)  (Dramatiq)
  → SourceService.execute_run
    → get_connector(source_key)   (solo mock | manual)
      → connector.search(page)    (reintentos ante TransientConnectorError)
        → RawListing (payload observado tal cual)
      → normalize(payload, source_key)  →  NormalizedListing + payload_hash
        → ListingService.ingest_raw  (transaccional, ADR-0012):
            (source_id, external_id) nuevo         → VehicleListing + RawListingPayload + ListingSnapshot
            payload_hash ya visto                  → solo refresca last_seen_at
            payload nuevo, listing conocido        → actualiza + snapshot si cambia precio·km·descripción
      → SourceSyncRun(SUCCESS | PARTIAL | FAILED, contadores, error saneado)
```

Cada fuente se aísla: reintentos acotados, fallo transitorio explícito e
idempotencia por `run_id`. Una caída deja el run en `PARTIAL`/`FAILED` sin
bloquear el resto. `RawListingPayload` es inmutable y nunca se expone por API.
La deduplicación entre fuentes y el scoring son fases posteriores.

## Petición autenticada de anuncios (Fase 2)

```text
GET /api/v1/listings?filtros   → require_auth → ListingRepository.search (join Source, filtros, orden, paginación)
GET /api/v1/listings/{id}      → require_auth → detalle + ListingSnapshot recientes
POST /api/v1/listings/manual   → require_csrf + rol OWNER|ADMIN → ManualEntryConnector.build_raw → ingest_raw
POST /api/v1/sources/{k}/sync  → require_csrf + rol OWNER|ADMIN
```

Los DTOs de salida nunca incluyen `payload` ni `payload_hash` (§36).

## Conocimiento y scoring previstos

```text
KnowledgeSource → Evidence validada → KnownIssue/Classification
Comparables observados → MarketEstimate(intervalo, confianza, cantidad)
Listing + Vehicle + MarketEstimate + Knowledge
  → ScoringProfileVersion inmutable
  → OpportunityScore(componentes + explicación + timestamp)
```

Se conserva la separación: observado, calculado, estimado, inferido y decidido manualmente. Una fuente D no puede verificar automáticamente un defecto. El score no usa IA y siempre referencia su versión.

## Compra y finanzas previstas

```text
Opportunity → OwnedVehicle → Expense ledger* → Sale
                     │             │
                     └──── cálculo transaccional ───► beneficio/ROI
```

Los totales se calculan desde movimientos; no se duplican como valores manuales. Los documentos fluyen por un `FileStorage` port, fuera del directorio público y tras autorización.

## Límites de confianza

- Navegador y proveedores externos son no confiables.
- Caddy añade límites/headers; FastAPI vuelve a validar.
- PostgreSQL conserva datos de negocio; Redis es efímero.
- Worker consume mensajes no confiables y vuelve a validar IDs/estado.
- Logs y métricas reciben metadatos saneados, nunca secretos o cuerpos completos.
