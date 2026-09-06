# ADR-0002: FastAPI como framework backend

- **Estado:** Aceptado
- **Fecha:** 2026-09-06

## Contexto

Se necesita API tipada, async para I/O, OpenAPI y ecosistema Python compatible con análisis de datos.

## Decisión

FastAPI con Pydantic v2, app factory, DTOs separados, dependencias explícitas y service layer.

## Alternativas

Django/DRF (más plataforma de la necesaria), Flask (más ensamblaje manual), Node/NestJS (rompe stack Python prescrito).

## Consecuencias

Contratos y validación sólidos con poca ceremonia. Deben evitarse lógica en routers, modelos ORM expuestos y llamadas síncronas dentro de handlers async.
