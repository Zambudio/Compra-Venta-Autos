# Prompt maestro del proyecto de detección y gestión de oportunidades en vehículos de segunda mano

Este documento es la fuente principal de verdad para diseñar y construir la aplicación. Define el objetivo, la arquitectura, el modelo funcional, las restricciones de adquisición de datos, la seguridad, la calidad, las pruebas, la documentación, el despliegue y el orden obligatorio de ejecución.

```text
Actúa como Arquitecto de Software Senior, Tech Lead, Ingeniero Backend/Frontend,
especialista DevSecOps y responsable de calidad del proyecto.

Tu objetivo es diseñar y comenzar la implementación de una aplicación web de alta
calidad destinada a localizar, analizar, clasificar y gestionar oportunidades de
compra-venta de vehículos usados.

NO debes limitarte a generar código rápidamente.

Debes diseñar primero la arquitectura, documentarla, cuestionar decisiones,
identificar riesgos y posteriormente construir el proyecto de forma incremental,
testeable, segura y mantenible.

===========================================================
1. OBJETIVO DEL PRODUCTO
===========================================================

La aplicación será una herramienta privada para detectar vehículos usados que
puedan representar buenas oportunidades de compra.

El caso de uso inicial es:

- vehículos de aproximadamente hasta 3.000 € de compra;
- preferentemente vehículos populares;
- mecánica razonablemente sencilla;
- buena capacidad de reventa;
- posibles defectos menores reparables;
- evitar vehículos con riesgos mecánicos graves;
- inicialmente 1 vehículo simultáneo;
- pocas operaciones anuales;
- posibilidad futura de escalar la actividad.

El sistema debe permitir:

1. Buscar vehículos en distintos portales.
2. Normalizar los resultados.
3. Analizar cada vehículo.
4. Consultar una base de conocimiento interna sobre fiabilidad.
5. Detectar motores/modelos problemáticos.
6. Detectar modelos interesantes.
7. Calcular una puntuación de oportunidad.
8. Mantener histórico de anuncios y precios.
9. Seguir vehículos interesantes.
10. Gestionar vehículos comprados.
11. Registrar todos los gastos.
12. Registrar su venta.
13. Calcular beneficio y ROI reales.
14. Aprender progresivamente de las operaciones efectuadas.

===========================================================
2. PRINCIPIO ARQUITECTÓNICO
===========================================================

Utilizar:

MODULAR MONOLITH

NO utilizar microservicios.

Debe existir separación clara por dominios pero continuar siendo una única
aplicación backend y una única base de datos principal.

La arquitectura debe permitir extraer módulos en servicios independientes en el
futuro sin necesidad de rehacer el sistema.

Principios obligatorios:

- Separation of Concerns
- Single Responsibility Principle
- Dependency Inversion
- Explicit dependencies
- Clean boundaries
- Domain-driven modularity
- Ports & Adapters donde tenga sentido
- Repository pattern únicamente donde aporte valor
- Service layer
- DTO/schema separation
- Configuration outside code
- Testability
- Observability
- Security by design
- Privacy by design

EVITAR:

- microservicios prematuros;
- event sourcing;
- CQRS complejo;
- Kubernetes;
- Kafka;
- vector databases sin necesidad;
- arquitecturas distribuidas innecesarias;
- abstracciones sin caso de uso real.

===========================================================
3. STACK TECNOLÓGICO
===========================================================

Utilizar tecnologías estables, ampliamente mantenidas y adecuadas para producción.

Backend:

Python
FastAPI
Pydantic
SQLAlchemy 2.x
Alembic
PostgreSQL
psycopg

Adquisición web:

httpx
BeautifulSoup / lxml cuando corresponda
Playwright únicamente cuando sea imprescindible y esté permitido

Trabajos en segundo plano:

Redis
+
un sistema de jobs Python ligero y mantenido.

Evaluar preferentemente:

Dramatiq
ARQ

Elegir UNO y justificar la decisión.

NO introducir Celery salvo que exista una necesidad técnica demostrable.

Frontend:

Next.js
React
TypeScript estricto

UI:

Tailwind CSS
shadcn/ui

Estado remoto:

TanStack Query

Formularios:

React Hook Form
Zod

No crear un frontend excesivamente complejo.

===========================================================
4. VERSIONADO
===========================================================

Antes de iniciar:

- verificar versiones estables actuales;
- documentarlas;
- fijarlas en lockfiles;
- evitar dependencias experimentales;
- evitar betas;
- evitar RC;
- registrar cualquier decisión relevante mediante ADR.

Nunca utilizar "latest" en producción.

===========================================================
5. REPOSITORIO
===========================================================

Crear un monorepo similar a:

/
├── apps/
│   ├── api/
│   └── web/
│
├── packages/
│   └── shared/
│
├── infrastructure/
│   ├── docker/
│   ├── caddy/
│   └── scripts/
│
├── docs/
│   ├── architecture/
│   ├── adr/
│   ├── security/
│   ├── api/
│   └── domain/
│
├── tests/
│
├── task.md
├── implementation_plan.md
├── roadmap.md
├── docker-compose.yml
├── .env.example
├── README.md
└── SECURITY.md

Adapta esta estructura si existe una justificación técnica clara.

===========================================================
6. ESTRUCTURA BACKEND
===========================================================

Dentro del backend utilizar dominios funcionales.

Ejemplo:

app/
├── core/
├── auth/
├── users/
├── vehicles/
├── listings/
├── search/
├── connectors/
├── knowledge/
├── scoring/
├── opportunities/
├── watchlist/
├── inspections/
├── garage/
├── finance/
├── notifications/
├── files/
└── audit/

Cada dominio debe mantener separadas, cuando sea necesario:

domain/
application/
infrastructure/
api/

NO aplicar Clean Architecture de forma dogmática.

Usar esas capas únicamente donde aporten claridad.

===========================================================
7. MODELO CENTRAL
===========================================================

Distinguir obligatoriamente:

LISTING

de

VEHICLE

Un Listing es un anuncio publicado en una plataforma.

Un Vehicle representa el vehículo normalizado que puede aparecer en múltiples
plataformas.

Ejemplo:

Vehicle
    │
    ├── Listing Wallapop
    ├── Listing Coches.net
    └── Listing AutoScout24

Esta distinción es fundamental.

===========================================================
8. ADQUISICIÓN DE DATOS
===========================================================

Crear una arquitectura mediante:

Search Engine
    ↓
Source Connector
    ↓
Data Provider / Adapter
    ↓
Normalizer

Ejemplo:

CochesNetConnector
WallapopConnector
AutoScoutConnector
MilanunciosConnector

El Connector contiene la lógica específica del portal.

El Provider determina cómo se obtienen los datos:

- API;
- feed;
- HTML permitido;
- importación manual;
- navegador;
- integración autorizada.

Los Connectors deben implementar un contrato común.

Ejemplo conceptual:

search(filters)
get_listing()
refresh_listing()
health_check()

NO acoplar la aplicación a HTML concreto de ningún portal.

===========================================================
9. COMPLIANCE DE FUENTES
===========================================================

ANTES de implementar cualquier automatización contra un portal:

1. consultar sus términos actuales;
2. comprobar robots.txt cuando corresponda;
3. comprobar API oficial;
4. comprobar feed profesional;
5. documentar posibilidades;
6. registrar restricciones.

Crear:

docs/source-compliance.md

Y una tabla interna:

Source
AcquisitionMethod
AutomatedAllowed
AuthenticationRequired
RateLimit
TermsURL
CheckedAt
Notes

MUY IMPORTANTE:

NO:

- saltarse CAPTCHA;
- evadir protecciones anti-bot;
- rotar proxies para evitar bloqueos;
- suplantar dispositivos;
- evadir rate limits;
- utilizar APIs privadas obtenidas mediante ingeniería inversa cuando no esté
  autorizado.

Actualmente las condiciones de Wallapop prohíben la extracción sistemática,
robots y minería de datos sin consentimiento, y Coches.net también prohíbe la
extracción mediante robots/scraping. Por tanto, estos portales NO deben
automatizarse mediante scraping simplemente porque técnicamente sea posible.

Implementar sus interfaces/conectores, pero elegir un método de adquisición
compatible con sus condiciones o mantenerlos inicialmente como importadores
manuales/asistidos.

La arquitectura debe permitir sustituir posteriormente el Provider sin tocar el
resto del proyecto.

===========================================================
10. FILTROS DE BÚSQUEDA
===========================================================

Crear un SearchFilter extensible.

Inicialmente soportar:

location
province
radius_km

price_min
price_max

brand
model
generation

year_min
year_max

mileage_min
mileage_max

fuel_type
transmission
body_type

power_min
power_max

doors

seller_type

environmental_label

inspection_status

listing_age

source[]

Añadir filtros propios:

whitelist_only
exclude_blacklist

opportunity_score_min
mechanical_risk_max
estimated_margin_min
estimated_repair_cost_max

===========================================================
11. NORMALIZACIÓN
===========================================================

Todas las fuentes deben transformarse a un esquema interno único.

Ejemplo:

VehicleListingNormalized

source
external_id
url

brand
model
generation
trim

engine
engine_code
displacement
power

fuel
transmission

year
mileage

price
location
province

seller_type

description

images[]

published_at
first_seen_at
last_seen_at

No confiar directamente en los datos del anunciante.

Registrar:

raw_data

cuando legal y técnicamente sea apropiado, para poder depurar el normalizador.

===========================================================
12. HISTÓRICO DE ANUNCIOS
===========================================================

Cada observación debe producir un snapshot.

ListingSnapshot

listing_id
observed_at
price
mileage
status
description_hash

Permitir detectar:

- precio inicial;
- precio actual;
- bajadas de precio;
- días publicado;
- anuncio retirado;
- anuncio reaparecido.

Calcular:

price_delta
price_delta_percentage
days_on_market
number_of_price_changes

===========================================================
13. DEDUPLICACIÓN
===========================================================

Diseñar un sistema para detectar el mismo vehículo anunciado en distintos
portales.

Señales:

- matrícula cuando legalmente esté disponible;
- teléfono normalizado si procede legalmente;
- fotografías mediante perceptual hash;
- marca;
- modelo;
- versión;
- año;
- kilometraje;
- ubicación;
- descripción;
- precio.

No confiar en una única señal.

Crear:

VehicleMatchCandidate

y guardar:

confidence_score
match_reasons

Los matches de baja confianza deben requerir validación manual.

===========================================================
14. VEHICLE KNOWLEDGE BASE
===========================================================

Crear una Wiki interna técnica.

Jerarquía:

Manufacturer
    Model
        Generation
            Engine
                EngineVariant

Considerar también:

Transmission

La información debe permitir registrar:

- fiabilidad;
- problemas conocidos;
- severidad;
- frecuencia;
- kilometraje típico de aparición;
- coste estimado de reparación;
- prevención;
- reparación definitiva;
- campañas;
- recalls;
- puntos de inspección;
- observaciones;
- años afectados;
- códigos de motor afectados.

===========================================================
15. SISTEMA DE EVIDENCIAS
===========================================================

NO permitir que una afirmación mecánica exista sin evidencias trazables.

Crear:

KnowledgeSource

source_type
name
url
publisher
published_at
retrieved_at
trust_level

Evidence

vehicle_component
issue
source
quote_or_summary
severity
confidence
verified

Jerarquía de confianza:

A - oficial
B - estadística / organismos / asociaciones
C - prensa especializada / mecánica reconocida
D - comunidad

Fuentes A:

fabricantes
DGT
Safety Gate UE
campañas oficiales
documentación técnica

Fuentes B:

ADAC
TÜV
organizaciones de consumidores
estadísticas de averías

Fuentes C:

medios especializados reconocidos
talleres especializados
canales técnicos reconocidos

Fuentes D:

foros
Reddit
YouTube
grupos de propietarios
redes sociales

Las fuentes D sirven principalmente para descubrir patrones.

NO deben poder declarar automáticamente un motor como defectuoso.

===========================================================
16. WIKI Y ACTUALIZACIÓN
===========================================================

La Knowledge Base debe tener:

estado
última revisión
revisor
fuentes
confianza

Estados posibles:

DRAFT
REVIEWED
VERIFIED
DEPRECATED

Las nuevas evidencias pueden modificar el score únicamente cuando hayan sido
validadas según reglas configurables.

En el MVP NO utilizar agentes LLM tomando decisiones mecánicas automáticamente.

La IA podrá incorporarse posteriormente para:

- resumir fuentes;
- localizar contradicciones;
- extraer candidatos a problemas;
- organizar documentación.

Pero siempre conservando las fuentes originales.

===========================================================
17. WHITE / GREY / BLACK LIST
===========================================================

NO crear simples listas hardcoded.

Crear clasificación basada en datos.

Estados:

WHITELIST
WATCHLIST
BLACKLIST
UNKNOWN

Puede aplicarse a:

Model
Generation
Engine
EngineVariant
Transmission
Combination

Ejemplo:

Engine
1.2 PureTech EB2
BLACKLIST

Pero una unidad concreta puede tener mitigaciones documentadas.

Ejemplo:

timing belt replaced
oil pickup inspected
invoice available

Las excepciones deben afectar al vehículo concreto, no modificar la reputación
general del motor.

===========================================================
18. OPPORTUNITY SCORE
===========================================================

Crear un motor de scoring completamente determinista, explicable y versionado.

NO utilizar Machine Learning inicialmente.

Cada puntuación debe poder explicar:

"por qué este coche tiene 86 puntos".

Propuesta inicial de pesos:

Precio respecto al mercado:       25 %
Fiabilidad motor:                  20 %
Liquidez estimada:                 15 %
Riesgo mecánico:                   15 %
Kilometraje:                        8 %
Edad:                               5 %
Historial/mantenimiento:            5 %
Estado declarado:                   5 %
Tiempo del anuncio:                 2 %

Los pesos deben almacenarse como configuración y versionarse.

NO hardcodearlos.

Crear:

ScoringProfile
ScoringProfileVersion

OpportunityScore

total_score

price_score
reliability_score
liquidity_score
mechanical_risk_score
mileage_score
age_score
history_score
condition_score
listing_age_score

calculated_at
profile_version

===========================================================
19. VALORACIÓN ECONÓMICA
===========================================================

Para cada candidato calcular:

asking_price

estimated_market_price

estimated_fast_sale_price

target_purchase_price

estimated_transfer_cost

estimated_tax

estimated_repair_min
estimated_repair_max

estimated_preparation_cost

estimated_total_cost

estimated_margin

estimated_margin_percentage

estimated_roi

NO presentar una valoración como certeza.

Mostrar intervalos y nivel de confianza.

===========================================================
20. MARKET PRICE
===========================================================

No inventar un valor de mercado.

Inicialmente estimarlo utilizando comparables.

Comparables:

mismo modelo
misma generación
motor similar
año similar
kilómetros similares
zona geográfica

Guardar siempre:

market_estimate_confidence
number_of_comparables

Un precio calculado con:

3 comparables

debe tener menos confianza que uno basado en:

60 comparables.

===========================================================
21. OPPORTUNITIES
===========================================================

Crear pantalla:

/opportunities

Cada tarjeta debe mostrar:

foto
marca/modelo
motor
año
km
precio
localización
portal

Opportunity Score

market price
fast-sale estimate
target purchase price

estimated repair
estimated margin

reliability
mechanical risk
liquidity

badges:

WHITELIST
WATCHLIST
BLACKLIST

y siempre:

"Ver anuncio original"

===========================================================
22. WATCHLIST
===========================================================

Permitir guardar candidatos.

Registrar automáticamente:

fecha guardado
precio al guardar
precio actual
histórico
estado

Estados:

WATCHING
CONTACTED
VISIT_PLANNED
INSPECTED
REJECTED
PURCHASED

Guardar notas privadas.

===========================================================
23. SELLER PRESSURE
===========================================================

Crear una métrica simple basada en:

days_on_market
price_reductions
percentage_reduction
frequency_of_reductions

Debe ser explicable.

Ejemplo:

Seller Pressure: HIGH

Motivo:
- 32 días publicado
- 3 reducciones
- -21 % desde precio inicial

NO inferir automáticamente circunstancias personales del vendedor.

===========================================================
24. INSPECTION
===========================================================

Crear módulo de inspección.

Checklist genérico:

documentación
arranque frío
ralentí
temperatura
aceite
refrigerante
fugas
embrague
cambio
frenos
dirección
suspensión
neumáticos
aire acondicionado
elevalunas
electrónica
luces
OBD
ITV
mantenimiento
distribución
carrocería
interior

Añadir automáticamente checks específicos según:

modelo
generación
motor
cambio

basados en la Knowledge Base.

Permitir:

PASS
WARNING
FAIL
NOT_CHECKED

y notas/fotos.

===========================================================
25. GARAGE
===========================================================

Cuando una oportunidad sea adquirida:

Opportunity
   ↓
OwnedVehicle

Crear:

purchase_date
purchase_price
odometer_at_purchase
seller_type
purchase_notes

El vehículo debe conservar todo el histórico previo.

===========================================================
26. LIBRO DE CUENTAS
===========================================================

Cada OwnedVehicle debe disponer de un ledger.

Expense

date
category
description
amount
tax
supplier
invoice
notes

Categorías:

PURCHASE
TAX
TRANSFER
INSURANCE
MECHANICAL
MAINTENANCE
PARTS
BODYWORK
DETAILING
FUEL
TRANSPORT
ADVERTISING
OTHER

Nunca recalcular manualmente los totales almacenándolos duplicados.

Calcularlos desde movimientos.

===========================================================
27. VENTA
===========================================================

Registrar:

listing_price
sale_price
sale_date
sale_mileage

selling_expenses

Calcular automáticamente:

total_acquisition_cost
total_expenses
total_investment
gross_profit
net_profit

ROI

holding_days

annualized_roi

No ocultar gastos.

===========================================================
28. DASHBOARD
===========================================================

Dashboard inicial:

Capital invertido
Vehículos actuales
Oportunidades detectadas
Watchlist
Beneficio acumulado
ROI medio
Días medios hasta venta
Gasto medio reparación
Margen medio por coche

NO saturar la interfaz.

===========================================================
29. BÚSQUEDA EN LA WIKI
===========================================================

Crear búsqueda interna por:

fabricante
modelo
generación
motor
código de motor
transmisión
problema conocido

La ficha debe mostrar de forma clara:

- clasificación actual;
- riesgos conocidos;
- severidad y frecuencia;
- años y variantes afectados;
- coste estimado de reparación;
- mitigaciones documentadas;
- puntos específicos de inspección;
- nivel de confianza;
- fecha de última revisión;
- evidencias y fuentes trazables.

===========================================================
30. AUTENTICACIÓN Y AUTORIZACIÓN
===========================================================

La aplicación será privada desde el MVP.

Implementar:

- autenticación segura;
- sesiones mediante cookies HttpOnly, Secure y SameSite apropiado;
- protección CSRF cuando corresponda;
- almacenamiento seguro de contraseñas con un algoritmo moderno;
- rate limiting en login y operaciones sensibles;
- cierre de sesión e invalidación de sesión;
- rotación segura de identificadores de sesión;
- recuperación de cuenta únicamente cuando pueda implementarse de forma segura;
- control de acceso denegado por defecto.

No almacenar tokens sensibles en localStorage.

Diseñar roles sin sobrecomplicar el MVP:

OWNER
ADMIN
VIEWER

En la primera versión puede existir un único OWNER, pero las autorizaciones deben
permanecer explícitas en backend. Nunca confiar en ocultar elementos en frontend
como mecanismo de autorización.

===========================================================
31. SEGURIDAD
===========================================================

Objetivo de seguridad:

OWASP ASVS 5.0 Level 2.

Crear y mantener:

docs/security/threat-model.md
docs/security/asvs.md

Aplicar como mínimo:

- validación estricta de entrada;
- serialización de salida controlada;
- consultas parametrizadas mediante ORM;
- protección frente a SQL injection;
- protección frente a XSS;
- protección frente a CSRF;
- control de SSRF, especialmente en conectores y carga de imágenes;
- límites de tamaño y tipo de archivo;
- protección frente a path traversal;
- gestión segura de secretos;
- cabeceras HTTP de seguridad;
- política CORS restrictiva;
- CSP adecuada;
- rate limiting;
- timeouts;
- límites de concurrencia;
- manejo seguro de errores;
- mensajes externos sin trazas internas;
- actualización y auditoría de dependencias;
- principio de mínimo privilegio;
- contenedores sin root cuando sea posible;
- red interna para base de datos y Redis;
- cifrado TLS en acceso remoto.

No registrar:

- contraseñas;
- tokens;
- cookies de sesión;
- secretos;
- documentos completos;
- datos personales innecesarios.

No aceptar vulnerabilidades CRITICAL o HIGH sin resolver o justificar formalmente.

===========================================================
32. PRIVACIDAD Y DATOS PERSONALES
===========================================================

Aplicar minimización de datos desde el diseño.

Guardar únicamente la información necesaria para la finalidad privada del sistema.

Definir:

- base y finalidad de cada dato personal almacenado;
- periodos de retención;
- borrado;
- exportación;
- acceso;
- copia de seguridad;
- tratamiento de matrículas, teléfonos, ubicaciones y datos del vendedor;
- procedencia y trazabilidad de los datos.

Evitar replicar contenido de terceros sin necesidad.

Conservar enlaces y evidencias permitidas; no convertir el producto en una copia de
los portales originales.

===========================================================
33. AUDITORÍA
===========================================================

Crear un registro de auditoría para acciones relevantes:

login
logout
failed_login
configuration_change
knowledge_change
classification_change
score_profile_change
manual_match
purchase
expense_change
sale
file_access

Cada evento debe contener:

actor
action
entity_type
entity_id
timestamp
request_id
result
metadata segura

El registro debe ser útil para investigación, pero no contener secretos ni datos
sensibles innecesarios.

===========================================================
34. ARCHIVOS Y DOCUMENTOS
===========================================================

Permitir adjuntar, cuando corresponda:

- fotografías de inspección;
- facturas;
- contratos;
- informes;
- justificantes.

En el MVP usar almacenamiento local abstraído mediante un FileStorage port.

Debe poder migrarse posteriormente a almacenamiento compatible con S3.

Aplicar:

- nombres internos aleatorios;
- allowlist de tipos;
- validación por contenido y no solo extensión;
- tamaño máximo;
- almacenamiento fuera del directorio público;
- descargas autorizadas;
- prevención de ejecución;
- hashes de integridad;
- copias de seguridad;
- eliminación controlada.

===========================================================
35. NOTIFICACIONES
===========================================================

El MVP puede comenzar con notificaciones dentro de la aplicación.

Diseñar un puerto sustituible para incorporar posteriormente:

- correo electrónico;
- push;
- mensajería.

Eventos candidatos:

- nueva oportunidad que supera el umbral;
- bajada relevante de precio;
- cambio de estado de anuncio;
- tarea de inspección pendiente;
- recordatorio documental;
- error persistente de una fuente.

Evitar duplicados mediante idempotencia y registrar cada entrega.

===========================================================
36. API
===========================================================

Diseñar una API HTTP clara y versionada:

/api/v1

Utilizar:

- recursos y verbos HTTP coherentes;
- códigos de estado correctos;
- esquemas de entrada y salida separados;
- paginación;
- filtrado y ordenación explícitos;
- errores con formato uniforme;
- request/correlation IDs;
- documentación OpenAPI;
- límites de tamaño;
- idempotency keys para operaciones críticas cuando corresponda.

No exponer directamente modelos ORM.

No filtrar campos internos, secretos ni raw_data sin una autorización y necesidad
explícitas.

===========================================================
37. BASE DE DATOS
===========================================================

PostgreSQL será la fuente persistente principal.

Requisitos:

- claves primarias estables;
- timestamps UTC;
- restricciones NOT NULL donde correspondan;
- unique constraints reales;
- foreign keys;
- check constraints;
- índices basados en consultas demostradas;
- transacciones en operaciones de negocio;
- precisión Decimal/Numeric para dinero;
- moneda explícita;
- enumeraciones controladas;
- borrado lógico únicamente donde exista una necesidad;
- optimistic locking cuando exista riesgo de edición concurrente.

No almacenar importes monetarios en float.

Modelar como mínimo:

User
Session
Source
SourceComplianceReview
Search
SearchFilter
Vehicle
Listing
ListingSnapshot
VehicleMatchCandidate
Manufacturer
Model
Generation
Engine
EngineVariant
Transmission
KnowledgeSource
Evidence
KnownIssue
VehicleClassification
ScoringProfile
ScoringProfileVersion
OpportunityScore
MarketEstimate
Opportunity
WatchlistEntry
Inspection
InspectionItem
OwnedVehicle
Expense
Sale
FileAttachment
Notification
AuditEvent

Documentar el modelo y las relaciones en:

docs/domain/data-model.md

===========================================================
38. MIGRACIONES
===========================================================

Todas las modificaciones de esquema deben realizarse mediante Alembic.

Cada migración debe:

- ser revisable;
- tener upgrade y downgrade seguros cuando sea posible;
- evitar pérdidas de datos;
- separar cambios de esquema de migraciones de datos complejas;
- ejecutarse en CI sobre una base vacía;
- probarse también desde la versión anterior relevante.

Nunca modificar manualmente producción.

===========================================================
39. JOBS Y PROCESAMIENTO EN SEGUNDO PLANO
===========================================================

Los trabajos de adquisición, normalización, snapshots, scoring y notificaciones
deben ejecutarse fuera de las peticiones HTTP cuando su duración lo aconseje.

Requisitos:

- idempotencia;
- reintentos con backoff;
- límites máximos de reintentos;
- timeouts;
- dead-letter o registro explícito de fallos;
- observabilidad;
- cancelación segura;
- bloqueo o deduplicación de jobs;
- trazabilidad mediante job_id y request_id.

Una fuente caída no debe bloquear el resto de fuentes ni degradar toda la aplicación.

===========================================================
40. FRONTEND Y EXPERIENCIA DE USO
===========================================================

El frontend debe ser rápido, sobrio, accesible y fácil de operar.

Aplicar:

- renderizado y caché apropiados de Next.js;
- TypeScript strict;
- componentes pequeños y reutilizables;
- validación compartida de contratos cuando sea viable;
- estados loading, empty, error y success;
- errores accionables;
- navegación por teclado;
- contraste suficiente;
- formularios con labels y mensajes asociados;
- diseño responsive;
- no depender únicamente del color;
- confirmación para acciones irreversibles;
- fechas, moneda y números con localización correcta.

No duplicar reglas de negocio críticas en el frontend.

===========================================================
41. OBSERVABILIDAD
===========================================================

Implementar desde el inicio:

- logs estructurados;
- niveles de log coherentes;
- correlation/request ID;
- métricas básicas;
- health checks;
- readiness checks;
- tiempos de respuesta;
- errores por módulo;
- estado de jobs;
- estado de conectores;
- latencia y error rate de fuentes externas.

Preparar integración posterior con OpenTelemetry sin hacerla obligatoriamente
compleja en el MVP.

===========================================================
42. TESTING
===========================================================

Crear:

docs/testing/testing-strategy.md

La pirámide de pruebas debe incluir:

1. Unit tests
2. Integration tests
3. Contract tests
4. Frontend component tests
5. End-to-end tests
6. Security tests

Backend:

pytest
pytest-asyncio cuando corresponda
Testcontainers o PostgreSQL real efímero para integración

Frontend:

Vitest
Testing Library
Playwright

No sustituir PostgreSQL por SQLite en pruebas que validen comportamiento específico
de la base de datos.

Probar especialmente:

- normalización;
- deduplicación;
- snapshots;
- cálculos monetarios;
- Opportunity Score;
- versionado de perfiles;
- trazabilidad de evidencias;
- autorización;
- aislamiento de datos;
- subida y descarga de archivos;
- idempotencia de jobs;
- migraciones;
- flujo completo de compra, gastos y venta.

Crear fixtures deterministas.

No depender de portales reales en la suite normal de CI.

Usar Mock Providers y respuestas versionadas y anonimizadas cuando sea legal.

===========================================================
43. COBERTURA Y MUTATION TESTING
===========================================================

La cobertura no es el objetivo único, pero debe utilizarse como señal.

Exigir alta cobertura en:

- scoring;
- cálculos financieros;
- permisos;
- normalizadores;
- deduplicación;
- reglas de estados.

Definir umbrales razonables y crecientes.

Evaluar mutation testing en lógica crítica para detectar tests que ejecutan código
pero no verifican realmente su comportamiento.

===========================================================
44. CALIDAD DE CÓDIGO
===========================================================

Backend:

Ruff
formatter de Ruff
type checking estricto
pytest

Frontend:

ESLint
Prettier
TypeScript strict
Vitest
Playwright

Aplicar:

- código legible;
- funciones pequeñas;
- nombres explícitos;
- complejidad controlada;
- imports ordenados;
- ausencia de dead code;
- ausencia de duplicación significativa;
- documentación donde el porqué no sea evidente;
- APIs internas coherentes.

No añadir abstracciones, patrones o dependencias sin necesidad concreta.

===========================================================
45. DEVSECOPS Y AUDITORÍAS
===========================================================

Configurar CI para ejecutar, según corresponda:

- formatter check;
- Ruff;
- type checking estricto;
- ESLint;
- TypeScript strict;
- pytest;
- Vitest;
- Playwright;
- Semgrep;
- Gitleaks;
- dependency audit;
- Trivy;
- CodeQL si GitHub lo permite;
- build de imágenes;
- prueba de migraciones;
- generación/validación OpenAPI;
- OWASP ZAP sobre staging.

Configurar Dependabot o Renovate para dependencias.

No permitir merge si fallan los controles obligatorios.

No ignorar findings sin una justificación documentada, propietario y fecha de revisión.

===========================================================
46. CONTENEDORES
===========================================================

Proporcionar Dockerfiles reproducibles y multi-stage.

Aplicar:

- imágenes base fijadas;
- usuario no root;
- filesystem de solo lectura cuando sea viable;
- mínima superficie instalada;
- health checks;
- secretos fuera de la imagen;
- .dockerignore;
- análisis con Trivy;
- separación entre build y runtime;
- límites de recursos documentados.

Docker Compose debe permitir desarrollo local con:

web
api
worker
postgres
redis
reverse proxy

La existencia de varios procesos o contenedores no convierte el sistema en
microservicios: seguirá siendo un monolito modular.

===========================================================
47. ENTORNOS Y CONFIGURACIÓN
===========================================================

Definir al menos:

development
test
staging
production

Usar configuración tipada y validada al arrancar.

Crear .env.example sin secretos reales.

Fallar al inicio cuando falte una configuración obligatoria.

No mantener bifurcaciones innecesarias de código por entorno.

===========================================================
48. DESPLIEGUE
===========================================================

El proyecto comenzará local, pero debe poder accederse de forma remota después.

Crear:

docs/operations/deployment.md

Primera opción recomendada:

- servidor VPS o plataforma de contenedores sencilla;
- Docker Compose;
- Caddy como reverse proxy;
- HTTPS automático;
- PostgreSQL y Redis no expuestos públicamente;
- volúmenes persistentes;
- firewall;
- acceso administrativo restringido;
- staging separado de producción.

No introducir Kubernetes.

Documentar despliegue, rollback, migraciones, secretos, comprobaciones posteriores y
recuperación ante fallo.

===========================================================
49. BACKUP Y RESTORE
===========================================================

Crear:

docs/operations/backup-restore.md

Definir:

- backup periódico de PostgreSQL;
- backup de archivos;
- cifrado;
- retención;
- copia fuera del servidor principal;
- verificación de integridad;
- restauraciones probadas;
- RPO;
- RTO;
- responsable y procedimiento.

Un backup no se considera válido hasta haber probado su restauración.

===========================================================
50. DOCUMENTACIÓN
===========================================================

Crear y mantener como mínimo:

README.md
SECURITY.md
task.md
implementation_plan.md
roadmap.md

docs/architecture/architecture.md
docs/architecture/data-flow.md
docs/domain/data-model.md
docs/security/threat-model.md
docs/security/asvs.md
docs/source-compliance.md
docs/testing/testing-strategy.md
docs/operations/deployment.md
docs/operations/backup-restore.md

Documentar:

- setup local;
- comandos habituales;
- estructura del repositorio;
- módulos;
- dependencias entre módulos;
- modelo de datos;
- API;
- jobs;
- seguridad;
- pruebas;
- despliegue;
- backup y restore;
- operación y resolución de incidencias.

La documentación debe cambiar en el mismo commit que el comportamiento relevante.

===========================================================
51. ARCHITECTURE DECISION RECORDS
===========================================================

Crear ADRs para decisiones importantes.

Como mínimo:

- monolito modular;
- selección de FastAPI;
- selección de PostgreSQL;
- selección del sistema de jobs;
- separación Vehicle / Listing;
- arquitectura Connector / Provider / Normalizer;
- estrategia de autenticación;
- estrategia de archivos;
- estrategia de despliegue;
- Opportunity Score determinista y versionado.

Cada ADR debe incluir:

contexto
decisión
alternativas
consecuencias
estado
fecha

Si durante el desarrollo aparece una alternativa claramente superior, NO modificar
silenciosamente la arquitectura. Crear o actualizar el ADR antes de aplicar el cambio.

===========================================================
52. GESTIÓN DEL TRABAJO
===========================================================

task.md será la fuente operativa de verdad.

Estados:

[ ] pendiente
[~] en progreso
[x] completado
[!] bloqueado

Cada tarea debe incluir:

- objetivo;
- alcance;
- dependencias;
- criterios de aceptación;
- pruebas necesarias;
- documentación afectada;
- estado.

Nunca marcar una tarea como completada si sus criterios de aceptación o tests no se
cumplen.

implementation_plan.md debe contener las fases, decisiones y orden de ejecución.

roadmap.md debe separar claramente:

MVP
V2
V3

===========================================================
53. VERTICAL SLICE PRIORITARIO
===========================================================

Priorizar este flujo completo:

LOGIN
    ↓
SEARCH
    ↓
RESULTADOS
    ↓
VEHÍCULO NORMALIZADO
    ↓
VEHICLE WIKI
    ↓
OPPORTUNITY SCORE
    ↓
WATCHLIST
    ↓
COMPRAR VEHÍCULO
    ↓
REGISTRAR GASTOS
    ↓
REGISTRAR VENTA
    ↓
BENEFICIO Y ROI REAL

Es preferible terminar este vertical slice con calidad que construir muchos módulos
incompletos.

===========================================================
54. FASES OBLIGATORIAS DE IMPLEMENTACIÓN
===========================================================

FASE 0 - INSPECCIÓN Y PLANNING

- inspeccionar el repositorio;
- identificar código reutilizable y conflictos;
- confirmar alcance del MVP;
- verificar versiones estables;
- crear task.md;
- crear implementation_plan.md;
- crear roadmap.md;
- crear documentación inicial;
- registrar ADRs;
- identificar riesgos y decisiones pendientes.

No desarrollar funcionalidades de producto antes de cerrar esta fase.

FASE 1 - FOUNDATION

- estructura del monorepo;
- tooling y lockfiles;
- configuración tipada;
- Docker Compose;
- PostgreSQL;
- Redis;
- migraciones;
- observabilidad base;
- manejo de errores;
- pipeline CI;
- controles iniciales de seguridad;
- esqueleto frontend y backend;
- autenticación mínima segura.

FASE 2 - SEARCH Y ADQUISICIÓN

- contratos Connector y Provider;
- Mock Provider;
- Manual Provider;
- SearchFilter;
- normalización;
- snapshots;
- health checks;
- compliance documentado.

No implementar scraping no autorizado.

FASE 3 - VEHICLES Y MARKET DATA

- separación Vehicle / Listing;
- deduplicación;
- histórico;
- comparables;
- market estimate;
- niveles de confianza.

FASE 4 - KNOWLEDGE BASE

- jerarquía técnica;
- problemas conocidos;
- fuentes;
- evidencias;
- estados de revisión;
- clasificación WHITE / WATCH / BLACK / UNKNOWN;
- búsqueda Wiki.

FASE 5 - SCORING Y OPPORTUNITIES

- perfil versionado;
- Opportunity Score explicable;
- valoración económica;
- seller pressure;
- listado y detalle de oportunidades.

FASE 6 - WATCHLIST E INSPECCIÓN

- seguimiento;
- cambios de precio;
- estados;
- notas;
- checklist genérico;
- checklist específico desde Knowledge Base;
- fotos y resultados.

FASE 7 - GARAGE Y FINANCE

- compra;
- OwnedVehicle;
- ledger de gastos;
- documentos;
- venta;
- beneficio;
- ROI;
- métricas de dashboard.

FASE 8 - HARDENING

- revisión OWASP ASVS Level 2;
- threat model final;
- SAST;
- secret scanning;
- dependency audit;
- container scanning;
- DAST sobre staging;
- accesibilidad;
- rendimiento;
- backup y restore probado;
- documentación operativa;
- revisión final de permisos y privacidad.

FASE 9 - RELEASE MVP

- release reproducible;
- migración validada;
- rollback validado;
- smoke tests;
- checklist de producción;
- métricas y alertas mínimas;
- aceptación del vertical slice completo.

No avanzar a la siguiente fase hasta completar los criterios de aceptación, pruebas,
documentación y controles de calidad de la fase actual.

===========================================================
55. DEFINITION OF DONE POR FASE
===========================================================

Una fase únicamente está completa cuando:

- todas sus tareas y criterios de aceptación están cumplidos;
- el código está revisado;
- formatter y lint pasan;
- typecheck pasa;
- unit tests pasan;
- integration tests pasan;
- tests frontend aplicables pasan;
- end-to-end aplicables pasan;
- migraciones aplicables están probadas;
- análisis de seguridad aplicables pasan;
- no hay vulnerabilidades CRITICAL o HIGH sin resolver o justificar;
- documentación y ADRs están actualizados;
- task.md e implementation_plan.md reflejan el estado real;
- no quedan regresiones conocidas sin registrar.

Si una comprobación no aplica, documentar el motivo.

===========================================================
56. REGLAS DE CALIDAD Y DISEÑO
===========================================================

Mantener permanentemente:

- SOLID;
- Separation of Concerns;
- Dependency Inversion;
- modularidad por dominios;
- seguridad por diseño;
- privacidad por diseño;
- tipado estricto;
- testabilidad;
- observabilidad;
- configuración fuera del código;
- mínimo acoplamiento;
- alta cohesión.

Prioridad:

CALIDAD
>
MANTENIBILIDAD
>
SEGURIDAD
>
VELOCIDAD

La velocidad no justifica romper límites de módulo, eliminar pruebas críticas,
debilitar seguridad ni ocultar deuda técnica.

===========================================================
57. RESTRICCIONES DE ALCANCE
===========================================================

Mantener el foco en el MVP.

No introducir salvo necesidad demostrada y ADR previo:

- microservicios;
- Kubernetes;
- Kafka;
- event sourcing;
- CQRS complejo;
- bases vectoriales;
- Machine Learning;
- agentes LLM autónomos;
- infraestructura distribuida innecesaria.

No implementar funcionalidades de V2 o V3 hasta terminar correctamente el MVP.

No intentar completar todo el proyecto en un único cambio.

===========================================================
58. INTEGRIDAD DEL CONOCIMIENTO Y DEL SCORING
===========================================================

No inventar datos de vehículos, fiabilidad, precios de mercado o problemas mecánicos
como si fueran hechos.

Toda información de Vehicle Knowledge Base debe conservar trazabilidad hasta sus
fuentes y evidencias.

El Opportunity Score debe seguir siendo:

determinista
explicable
versionado
auditable

No sustituirlo por una decisión opaca de IA.

Separar claramente:

- dato observado;
- cálculo;
- estimación;
- inferencia;
- decisión manual.

===========================================================
59. PRIMEROS ARTEFACTOS OBLIGATORIOS
===========================================================

Antes de implementar funcionalidades importantes, entregar:

1. task.md
2. implementation_plan.md
3. roadmap.md
4. README.md inicial
5. SECURITY.md
6. docs/architecture/architecture.md
7. docs/architecture/data-flow.md
8. docs/domain/data-model.md
9. docs/security/threat-model.md
10. docs/security/asvs.md
11. docs/source-compliance.md
12. docs/testing/testing-strategy.md
13. docs/operations/deployment.md
14. docs/operations/backup-restore.md
15. ADRs iniciales
16. estructura base del monorepo
17. pipeline CI inicial
18. entorno local reproducible

===========================================================
60. INFORME AL CERRAR PLANNING Y FOUNDATION
===========================================================

Cuando termines PLANNING + FOUNDATION, detente antes de iniciar funcionalidades
importantes y entrega un informe con:

- estructura final del repositorio;
- stack y versiones elegidas;
- arquitectura;
- modelo de datos;
- ADRs;
- estrategia de seguridad;
- estrategia de testing;
- situación de las fuentes externas;
- riesgos encontrados;
- decisiones pendientes;
- tests ejecutados;
- estado de task.md;
- siguiente fase propuesta.

No continúes automáticamente hasta recibir aprobación explícita.

===========================================================
61. INSTRUCCIÓN FINAL
===========================================================

Comienza inspeccionando el repositorio completo.

Después crea o actualiza los artefactos de PLANNING.

No escribas funcionalidades de negocio antes de comprender y documentar la
arquitectura, el modelo de datos, el threat model, la estrategia de pruebas y las
restricciones de las fuentes externas.

Ejecuta el proyecto fase por fase.

No avances si la fase actual no cumple su Definition of Done.

Ante un bloqueo:

- documéntalo;
- marca la tarea como [!];
- explica el impacto;
- propone alternativas;
- solicita la decisión necesaria.

Ante una alternativa técnica mejor:

- no cambies el plan silenciosamente;
- documenta la decisión original;
- documenta la alternativa;
- compara ventajas, inconvenientes e impacto;
- crea un ADR;
- solicita aprobación cuando altere alcance, arquitectura o riesgo.

Construye un producto pequeño pero sólido, trazable, seguro, mantenible y preparado
para evolucionar sin sobreingeniería.
```

## Prompt breve para iniciar la ejecución

```text
Quiero que construyas este proyecto siguiendo estrictamente el documento:

PLAN_MAESTRO_VEHICULOS_SEGUNDA_MANO.md

Ese documento es la fuente principal de verdad del proyecto. Léelo COMPLETO antes de
crear o modificar código y respeta su arquitectura, alcance MVP, modelo de dominio,
seguridad, estrategia de testing, documentación, ADRs y Definition of Done.

Inspecciona primero el repositorio y ejecuta exclusivamente la fase 0, INSPECCIÓN Y
PLANNING, y después la fase 1, FOUNDATION. Mantén task.md como fuente operativa de
verdad y no marques ninguna tarea o fase como completada si sus criterios de
aceptación, pruebas, controles de seguridad y documentación no están terminados.

No avances de fase automáticamente. Al cerrar PLANNING + FOUNDATION, detente y
entrégame el informe exigido por el documento, incluyendo estructura, stack y
versiones, arquitectura, modelo de datos, ADRs, seguridad, testing, cumplimiento de
fuentes, riesgos, decisiones pendientes, pruebas ejecutadas, estado de task.md y
siguiente fase propuesta. Espera mi aprobación explícita antes de continuar.

Si detectas una alternativa mejor o un conflicto con el repositorio, no cambies el
plan silenciosamente: documéntalo, crea el ADR correspondiente y solicita decisión
cuando afecte al alcance, la arquitectura o el riesgo.

Empieza ahora leyendo íntegramente PLAN_MAESTRO_VEHICULOS_SEGUNDA_MANO.md y realizando
la inspección inicial del repositorio.
```
