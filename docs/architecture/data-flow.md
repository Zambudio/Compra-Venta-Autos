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

## Adquisición prevista (Fase 2)

```text
SearchFilter validado
  → SearchApplicationService
    → Connector por Source
      → Provider autorizado (Mock/Manual en MVP inicial)
        → payload observado
      → Normalizer
        → VehicleListingNormalized + raw_data permitido
          → Listing upsert + ListingSnapshot append-only
            → job de deduplicación/scoring (fases posteriores)
```

Cada fuente se aísla: timeout, rate limit, circuit/fallo explícito e idempotencia. Una caída no bloquea las demás. `raw_data` solo se guarda si la base legal, minimización y términos lo permiten.

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
