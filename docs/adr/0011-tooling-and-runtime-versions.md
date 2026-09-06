# ADR-0011: tooling y runtimes fijados

- **Estado:** Aceptado
- **Fecha:** 2026-09-06

## Contexto

El monorepo necesita instalaciones rápidas, lockfiles y compatibilidad entre desarrollo, CI y contenedores.

## Decisión

Python 3.14 (imagen 3.14.7) con `uv` 0.10.2 y `uv.lock`; Node 24 LTS (24.20.0) con pnpm 11.1.3 y workspace/lockfile. Dependencias directas exactas; imágenes con versión y digest.

## Alternativas

pip/requirements (resolución menos integrada), Poetry (más coste sin ventaja aquí), npm/yarn (válidos pero pnpm optimiza workspace), Node Current 26 (no LTS al decidir).

## Consecuencias

Builds reproducibles y actualización explícita. Python local 3.14.4 puede ejecutar el rango 3.14, pero CI/contenedor fijan 3.14.7. Renovaciones pasan por tests y auditorías.

El workspace reside en un recurso UNC/NAS de Windows que rechazó los symlinks del linker aislado de pnpm (`ERR_PNPM_UNKNOWN symlinkAllModules`). Se usa `node-linker=hoisted`, configuración oficial compatible con filesystems sin symlinks. Se mantiene pnpm y el lockfile; el coste es menor aislamiento físico entre dependencias, compensado por workspace, pins exactos, strict peers y CI.
