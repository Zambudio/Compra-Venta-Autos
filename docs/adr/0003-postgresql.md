# ADR-0003: PostgreSQL como persistencia principal

- **Estado:** Aceptado
- **Fecha:** 2026-09-06

## Contexto

El dominio requiere integridad relacional, transacciones, JSONB controlado, precisión monetaria y consultas históricas.

## Decisión

PostgreSQL 18 con SQLAlchemy 2.x, psycopg 3 y Alembic. UUID, UTC, `Numeric`, FK/unique/check constraints reales.

## Alternativas

SQLite (no representa concurrencia/tipos de producción), MySQL, bases documentales.

## Consecuencias

Integridad y capacidad de consulta fuertes; exige servicio PostgreSQL real en integración y operación de backups/migraciones.
