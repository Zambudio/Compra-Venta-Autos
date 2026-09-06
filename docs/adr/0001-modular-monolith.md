# ADR-0001: monolito modular

- **Estado:** Aceptado
- **Fecha:** 2026-09-06

## Contexto

El MVP es privado, de bajo volumen y necesita límites de dominio claros sin coste distribuido.

## Decisión

Una aplicación FastAPI, una base PostgreSQL y módulos por dominio. Web y worker son procesos desplegables del mismo monorepo; el worker comparte código y contratos.

## Alternativas

Microservicios; monolito por capas técnicas sin módulos; serverless por función.

## Consecuencias

Transacciones y operación simples, despliegue económico y refactor incremental. Exige disciplina de imports y ownership; un módulo podrá extraerse solo tras demostrar necesidad.
