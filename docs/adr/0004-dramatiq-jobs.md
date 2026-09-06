# ADR-0004: Dramatiq para jobs

- **Estado:** Aceptado
- **Fecha:** 2026-09-06

## Contexto

Adquisición, snapshots, scoring y notificaciones necesitan ejecutarse fuera de HTTP. El Plan pide evaluar Dramatiq y ARQ, sin Celery salvo necesidad.

## Decisión

Dramatiq 2.2 con broker Redis. Los actores serán pequeños, idempotentes y llamarán servicios de aplicación. Foundation solo crea broker/worker y observabilidad mínima.

## Alternativas

ARQ ofrece una integración asyncio muy ligera, pero su cadencia/mantenimiento y menor ecosistema operativo presentan más riesgo. Celery aporta funciones no necesarias y mayor complejidad. Tareas in-process pierden durabilidad/aislamiento.

## Consecuencias

API simple, retries/middleware y aislamiento por proceso. Hay que diseñar idempotency keys, límites, backoff, dead-letter explícito y propagación de `job_id/request_id` antes de jobs reales.
