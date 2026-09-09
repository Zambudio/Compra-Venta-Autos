# ADR-0015: Opportunity Scoring determinista, explicable y versionado, y Valoración Económica con intervalos de confianza

- **Estado:** Aceptado
- **Fecha:** 2026-09-09
- **Relacionado con:** ADR-0010, ADR-0013, ADR-0014

## Contexto

El Plan Maestro (§18–§21, §23) establece que el núcleo de valor de MotorScope para la toma de decisiones de compra-venta es la identificación rápida y objetiva de oportunidades rentables y seguras.
Para evitar sesgos subjetivos, compras impulsivas o errores de cálculo financiero en vehículos usados de segunda mano (target inicial: vehículos populares de hasta ~3.000 € en España), se requiere:

1. **Determinismo absoluto y explicabilidad:** todo cálculo de puntuación debe ser reproducible y descomponible. Cada puntuación debe responder con precisión a la pregunta: *"¿por qué este coche tiene X puntos?"*.
2. **Cero Machine Learning y cero agentes LLM decisores:** en el MVP no se emplean redes neuronales opacas ni modelos generativos para decidir si un coche es una oportunidad o valorar su precio (Plan Maestro §18).
3. **Ponderación configurable, versionada e inmutable:** los pesos de los componentes no pueden estar hardcodeados en código. Deben residir en perfiles (`ScoringProfile`) con versiones inmutables (`ScoringProfileVersion`), donde la suma de pesos sea estrictamente 1.000 (100%). Cada cálculo persiste la versión utilizada para garantizar auditoría histórica.
4. **Valoración económica con intervalos de confianza:** ninguna proyección financiera puede presentarse como una certeza matemática infalible (Plan Maestro §19). Los costes de reparación, margen neto y retorno sobre la inversión (ROI) deben expresarse en intervalos (mínimo–máximo) y acompañarse de un nivel de confianza derivado de la homogeneidad y volumen de comparables.
5. **Estimación realista de costes en España:** cálculo estructurado de costes de transferencia (Impuesto de Transmisiones Patrimoniales ITP + tasa DGT de cambio de titularidad), reacondicionamiento y preparación básica, y reparaciones mecánicas estimadas a partir de los fallos conocidos de la Knowledge Base (Fase 4).
6. **Métrica explicable de presión del vendedor:** indicador objetivo de urgencia de venta basado en días en mercado y trayectoria de bajadas de precio (Plan Maestro §23), sin inferir especulaciones personales del vendedor.

## Decisión

### 1. Modelo de Datos de Scoring y Versiones
- `ScoringProfile`: catálogo de estrategias de inversión (p. ej. *Oportunidad Reventa Rápida*, *Perfil Conservador*, *Perfil Básico*).
- `ScoringProfileVersion`: versión inmutable de un perfil con:
  - `weights`: JSONB con los 9 componentes obligatorios que suman exactamente 1.000.
  - `config`: JSONB con parámetros operativos (umbrales de días en venta, recargo ITP por defecto, etc.).
  - `is_immutable`: booleano que impide mutar versiones tras ser utilizadas en evaluaciones.
- `OpportunityScore`: cálculo persistente e inmutable:
  - Referencia a `vehicle_id`, `listing_id` y `profile_version_id`.
  - `total_score` (0.00 a 100.00).
  - Subscores individuales (0.00 a 100.00) para cada uno de los 9 componentes.
  - `score_breakdown`: desglose explicable en JSONB con valor observado, puntuación parcial, peso ponderado, contribución al total y justificación textual detallada.
  - `calculated_at`: timestamp UTC de evaluación.

### 2. Los 9 Componentes del Opportunity Score (Plan Maestro §18)
La versión inicial del perfil de referencia distribuye el 100% de la puntuación en 9 factores:
1. **Precio respecto al mercado (`price_score`, 25%):** contraste del precio pedido (`asking_price`) contra el precio de mercado (`MarketEstimate` calculado con filtro IQR en Fase 3). Puntuación alta si asking está por debajo del percentil 25 o ratio asking/market < 0.80.
2. **Fiabilidad de motor (`reliability_score`, 20%):** integración directa con la Knowledge Base de Fase 4 (`WHITELIST` = 100, `UNKNOWN` = 60, `WATCHLIST` = 35, `BLACKLIST` = 0).
3. **Liquidez estimada (`liquidity_score`, 15%):** demanda comercial esperada en el mercado español según segmento, marca, modelo y combustible (utilitarios y compactos diésel/gasolina populares tienen máxima rotación).
4. **Riesgo mecánico (`mechanical_risk_score`, 15%):** afecciones técnicas y campañas de retirada registradas en `KnownIssue` (Fase 4) no mitigadas en la unidad. La existencia de `VehicleMitigation` documentadas recupera la puntuación.
5. **Kilometraje (`mileage_score`, 8%):** desviación de los kilómetros reales frente al kilometraje esperado según edad y motorización (~15.000 km/año diésel, ~10.000 km/año gasolina en España). Penalización progresiva a partir de 220.000 km.
6. **Edad (`age_score`, 5%):** curva de depreciación y antigüedad. Valoración favorable para el rango óptimo del caso de uso (8 a 16 años, mantenimiento simple) y penalización por obsolescencia ambiental o extrema antigüedad (>22 años).
7. **Historial de anuncios (`history_score`, 5%):** estabilidad temporal observada en `ListingSnapshot` (reapariciones erráticas o subidas de precio penalizan; bajadas de precio reflejan seguimiento favorable).
8. **Estado declarado (`condition_score`, 5%):** análisis de señales objetivas en descripción y equipamiento (ITV en vigor, libro de revisiones, kit de distribución recién cambiado vs palabras clave de avería declarada).
9. **Tiempo del anuncio y negociación (`listing_age_score`, 2%):** antigüedad de publicación en portal combinada con la presión del vendedor.

### 3. Presión del Vendedor (`SellerPressure`)
Métrica determinista calculada a partir de los snapshots del anuncio:
- Variables: `days_on_market`, número de reducciones de precio, porcentaje acumulado de rebaja.
- Niveles: `LOW`, `MEDIUM`, `HIGH`.
- Explicabilidad: lista estructurada de motivos (ej. *"32 días publicado, 2 bajadas de precio, -15.4% de descuento acumulado"*).
- Prohibición expresa de inferir motivos personales subjetivos.

### 4. Entidad y Valoración Económica (`Opportunity`)
Entidad comercial vinculada al vehículo y su anuncio principal:
- Estados de ciclo de vida: `IDENTIFIED` (detectada automáticamente), `ANALYZING` (en revisión activa), `VALIDATED` (confirmada como opción real de compra), `DISCARDED` (descartada con motivo).
- Parámetros financieros en precisión `Decimal` (`Numeric(12, 2)`):
  - `asking_price`: precio publicado.
  - `estimated_market_price`: precio de mercado de referencia.
  - `estimated_fast_sale_price`: precio de salida rápida (< 30 días, típicamente P25 de comparables o ~88% de mercado).
  - `target_purchase_price`: oferta objetivo recomendada para preservar el margen deseado.
  - `estimated_transfer_cost`: ITP (4% a 8% según fiscalidad) + tasa de cambio de titularidad DGT (tasa fija oficial ~55,70 €).
  - `estimated_preparation_cost`: acondicionamiento básico (limpieza integral, diagnosis, fluidos básicos: ~150–250 €).
  - `estimated_repair_min` / `estimated_repair_max`: intervalo de reparación preventiva/correctiva derivado de los problemas conocidos no mitigados de Fase 4.
  - `estimated_total_cost_min` / `max`: coste acumulado de adquisición y puesta a punto.
  - `estimated_margin_min` / `max`: beneficio neto proyectado en venta rápida.
  - `estimated_roi_min` / `max`: porcentaje de retorno sobre la inversión total requerida.
  - `confidence_level`: `LOW` (< 5 comparables o datos incompletos), `MEDIUM` (5 a 14 comparables), `HIGH` (>= 15 comparables con baja dispersión).

### 5. Interfaz de Usuario (/opportunities)
- Vista `/opportunities` con filtrado por estado, score mínimo, nivel de presión y marca.
- Tarjetas accesibles con todos los datos clave (Plan Maestro §21).
- Desglose explicable del score por componentes mediante panel accesible.
- Enlace directo al anuncio original con atributos de seguridad (`rel="noopener noreferrer"`).
- Integración en la vista de detalle del vehículo y anuncio.

## Consecuencias

- **Positivas:**
  - Evaluaciones 100% reproducibles y auditables para cualquier vehículo o anuncio en cualquier momento histórico.
  - Protección del capital de compra al evitar compras basadas en optimismo no fundamentado mediante intervalos mínimos y máximos.
  - Integración sinérgica de los módulos de Fase 2 (anuncios y snapshots), Fase 3 (comparables y mercado IQR) y Fase 4 (Knowledge Base y fiabilidad de motores).
- **Limitaciones controladas:**
  - Si una unidad carece de comparables suficientes en la BD, la valoración económica advertirá un nivel de confianza bajo (`confidence_level = LOW`) y requerirá revisión manual del usuario antes de validar la oportunidad.
