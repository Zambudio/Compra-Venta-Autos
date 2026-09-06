# ADR-0013: Modelo de Vehicle, matching determinista asistido y estimación de mercado

- **Estado:** Aceptado
- **Fecha:** 2026-09-06

## Contexto

La Fase 2 completó la ingesta normalizada de anuncios en `VehicleListing` con snapshots de histórico, pero sin asociar anuncios al vehículo físico subyacente (`Vehicle`). Para la Fase 3 se requiere:
1. Distinguir la identidad del vehículo de sus anuncios (Plan Maestro §7, ADR-0005).
2. Deduplicar anuncios del mismo vehículo procedentes de distintas fuentes (Plan Maestro §13).
3. Calcular métricas de histórico sin duplicar datos en persistencia (Plan Maestro §12).
4. Estimar el valor de mercado mediante comparables reales y objetivos (Plan Maestro §20).

Restricciones legales y de diseño:
- R-03 / Privacidad: CERO uso de matrículas ni números de teléfono en el matching automático.
- Cero Machine Learning opaco: algoritmos puramente deterministas, explicables y con razones auditables.
- Enfoque asistido: los candidatos se presentan para validación humana (OWNER/ADMIN); no se fusionan anuncios de forma destructiva o no supervisada.

## Decisión

### 1. Entidad Vehicle y asociación tardía
- `Vehicle` es la entidad normalizada de un coche físico: marca, modelo, generación, versión/trim, código de motor, combustible, transmisión, año de matriculación y contadores agregados (`first_listed_at`, `listing_count`).
- `VehicleListing.vehicle_id` es una clave foránea nullable con `ondelete="SET NULL"`. No se migran datos destructivamente.

### 2. Candidatos de matching (`VehicleMatchCandidate`)
- Representa una propuesta de unión entre dos anuncios (`listing_a_id < listing_b_id` para garantizar unicidad de par) o un anuncio y un vehículo.
- Estados: `PENDING`, `CONFIRMED`, `REJECTED`.
- Función de matching pura: `score_match(listing_a, listing_b) -> MatchResult(confidence, reasons)`.
- Señales y ponderaciones:
  - Marca: coincidencia canónica requerida (filtro estricto).
  - Modelo: similitud normalizada (peso 0.25).
  - Año: tolerancia estricta (0 años diff = 1.0, 1 año = 0.5, >1 = 0.0) (peso 0.20).
  - Combustible y Transmisión: coincidencia requerida (peso 0.15).
  - Kilometraje: diferencia relativa (peso 0.15).
  - Precio: diferencia relativa (peso 0.10).
  - Ubicación/Provincia: misma provincia suma confianza (peso 0.05).
  - Descripción: solapamiento léxico normalizado (peso 0.10).
- Umbral: pares con confianza >= 0.60 generan `VehicleMatchCandidate` en estado `PENDING`.
- Toda confirmación o rechazo manual es ejecutada por `OWNER|ADMIN`, emite `AuditEvent` (`manual_match`) y enlaza o desvincula los `vehicle_id`.

### 3. Histórico derivado sin redundancia
- A partir de `ListingSnapshot`, se calculan métricas al vuelo: `price_delta`, `price_delta_percentage`, `days_on_market`, `number_of_price_changes`, precio inicial y precio actual.
- A nivel de `Vehicle`, se agrega la evolución consolidada de todos sus anuncios activos.

### 4. Estimación de mercado (`MarketEstimate`)
- Pool de comparables extraído de los anuncios homogéneos en la BD (misma marca/modelo, combustible idéntico, año ±2, kilometraje ±30%).
- Cálculo determinista: exclusión de outliers con rango intercuartil (IQR), mediana como importe estimado (`estimated_amount`), P25 como cota inferior (`low_amount`) y P75 como cota superior (`high_amount`).
- Confianza estadística (`confidence_score`): función sigmoide/proporcional al tamaño de la muestra ($N$) y penalizada por la dispersión relativa (IQR / mediana).
- Nunca se inventa precio ni se presenta como certeza matemática; se expone siempre el intervalo y el número de comparables.

## Alternativas descartadas
- Deduplicación totalmente automática sin revisión humana: descartada por riesgo de falsos positivos irreversibles sin matrículas.
- Uso de ML/embeddings para matching en Fase 3: descartado por romper el principio de determinismo y explicabilidad del MVP (Plan Maestro §57).
- Almacenamiento redundante de deltas de precio en columnas de tabla: descartado para evitar desincronizaciones de datos con los snapshots.

## Consecuencias
- Esquema limpio y no destructivo (`20260906_0004`).
- Trazabilidad y auditoría completa de cualquier fusión de anuncios.
- Interfaz accesible y transparente para que el usuario controle la deduplicación y entienda cómo se calcula el valor de mercado.
