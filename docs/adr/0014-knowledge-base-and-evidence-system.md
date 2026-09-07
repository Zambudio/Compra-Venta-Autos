# ADR-0014: Jerarquía técnica de vehículos, base de conocimiento y sistema de evidencias

- **Estado:** Aceptado
- **Fecha:** 2026-09-07

## Contexto

El Plan Maestro (§14–§17) establece que uno de los pilares de valor de MotorScope es el análisis preventivo de riesgos mecánicos antes de la adquisición.
Para evitar comprar vehículos con fallos catastróficos conocidos (p. ej. motores con problemas graves de distribución o diseño defectuoso) y detectar oportunidades de modelos fiables de bajo coste, se requiere una base de conocimiento técnica interna.

Restricciones y principios obligatorios:
1. **Ninguna afirmación sin evidencia:** ninguna afirmación mecánica puede existir en el sistema sin fuentes trazables y verificables (Plan Maestro §15).
2. **Jerarquía técnica estructurada:** la información mecánica no se asocia como texto libre al azar, sino a una jerarquía canónica: Manufacturer -> Model -> Generation -> Engine -> EngineVariant y transmisiones asociables (Plan Maestro §14).
3. **Gradación de confianza de fuentes:** categorización formal de fuentes en niveles A (oficial / campañas de fabricantes / Safety Gate UE), B (estadísticas / TÜV / ADAC / asociaciones de consumidores), C (prensa especializada / talleres y canales técnicos reconocidos) y D (comunidad / foros / usuarios) (Plan Maestro §15).
4. **Clasificación basada en datos:** no crear listas negras hardcodeadas en código; usar clasificación explicable y versionada (WHITELIST, WATCHLIST, BLACKLIST, UNKNOWN) aplicable a modelos, generaciones, motores, variantes o transmisiones (Plan Maestro §17).
5. **Mitigaciones a nivel de unidad:** las reparaciones o sustituciones preventivas documentadas en un vehículo concreto (ej. factura de cambio de correa o tensor) mitigan el riesgo de esa unidad, pero nunca alteran la reputación general del motor en la Wiki técnica (Plan Maestro §17).
6. **Cero agentes LLM decisores en MVP:** en el MVP no se emplean modelos generativos para decidir mecánicamente de forma autónoma (Plan Maestro §16).

## Decisión

### 1. Jerarquía técnica de catálogo
- Manufacturer: fabricante (marca normalizada, país de origen, etc.).
- VehicleModel: modelo perteneciente a un fabricante.
- VehicleGeneration: generación acotada por años de fabricación (year_start, year_end).
- Engine: familia/código base de motor (código de motor, nombre, cilindrada displacement_cc, tipo de combustible, aspiración).
- EngineVariant: variante de motor con potencia (power_kw, power_cv), par motor (	orque_nm), y período de vigencia.
- TransmissionSpec: tipo de caja de cambios (manual, automática convertidor, doble embrague, CVT) y marchas.

### 2. Fuentes y Sistema de Evidencias
- KnowledgeSource: registro inmutable de la fuente de información: source_type (OFFICIAL_RECALL|STATISTICAL_REPORT|TECHNICAL_MEDIA|COMMUNITY_REPORT), 
ame, url, publisher, published_at, 
etrieved_at y 	rust_level (A|B|C|D).
- Evidence: fragmento probatorio concreto vinculado a una fuente: component (p. ej. TIMING_BELT, TURBOCHARGER, OIL_PICKUP, INJECTORS, EGR), summary, severity (LOW|MEDIUM|HIGH|CRITICAL), confidence_score (0.00 a 1.00) y flag erified.

### 3. Problemas Conocidos (KnownIssue)
- Representa una afección técnica diagnosticada:
  - Atributos: 	itle, description, component, severity (LOW|MEDIUM|HIGH|CRITICAL), requency (RARE|OCCASIONAL|FREQUENT|SYSTEMIC), 	ypical_mileage_km, estimated_repair_cost_min, estimated_repair_cost_max, symptoms, prevention, definitive_repair.
  - Estados del ciclo de vida: DRAFT, REVIEWED, VERIFIED, DEPRECATED.
  - Relaciones: vinculado a múltiples Evidence que lo respaldan, y asociado a los motores, generaciones o transmisiones afectados.

### 4. Clasificación de Fiabilidad (White / Watch / Blacklist)
- VehicleClassification:
  - 	arget_type: MODEL, GENERATION, ENGINE, ENGINE_VARIANT, TRANSMISSION, COMBINATION.
  - 	arget_id: identificador UUID del elemento clasificado.
  - status: WHITELIST, WATCHLIST, BLACKLIST, UNKNOWN.
  - 
ationale: justificación técnica documentada basada en evidencias.
  - Período de vigencia opcional (alidity_start, alidity_end).

### 5. Motor de Detección y Consulta de Fiabilidad
- Servicio KnowledgeService.lookup_vehicle_reliability(brand, model, year, fuel_type, engine_code):
  - Resuelve la mejor coincidencia en la jerarquía técnica.
  - Recupera todos los KnownIssue verificados aplicables.
  - Determina la clasificación vigente (WHITELIST, WATCHLIST, BLACKLIST, UNKNOWN).
  - Calcula el riesgo mecánico agregado y el rango de costes estimados de reparación preventiva/correctiva.
  - Identifica las mitigaciones documentadas que el usuario debe buscar o verificar en una unidad de segunda mano.

## Alternativas descartadas
- Listas estáticas en archivos de configuración YAML/JSON: descartadas porque no permiten trazabilidad de evidencias, auditoría, ni consultas cruzadas en base de datos.
- Extracción autónoma de problemas mediante scraping no supervisado o LLM: descartada expresamente por el Plan Maestro para evitar alucinaciones y diagnósticos mecánicos erróneos.
- Fusión de problemas conocidos en columnas de Vehicle: descartada porque un problema mecánico es un concepto de conocimiento general compartido por miles de vehículos de una misma motorización.

## Consecuencias
- Esquema relacional estructurado mediante migración Alembic 20260907_0005_knowledge_base.py.
- Base de datos enriquecida con casos de referencia contrastados del mercado español.
- Capacidad para que las fases posteriores (Scoring y Oportunidades en Fase 5, Inspecciones en Fase 6) consuman directamente los riesgos mecánicos y los costes estimados de la Knowledge Base.
