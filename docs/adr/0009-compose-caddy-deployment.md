# ADR-0009: despliegue Docker Compose con Caddy

- **Estado:** Aceptado
- **Fecha:** 2026-09-06

## Contexto

El sistema empieza local y debe poder desplegarse remotamente con poca carga operativa.

## Decisión

Imágenes multi-stage fijadas; Compose para web/api/worker/PostgreSQL/Redis/Caddy; Caddy termina TLS y es el único servicio público. Primera producción en VPS/plataforma simple.

## Alternativas

Kubernetes (sobreingeniería), PaaS por servicio (más acoplamiento), instalar procesos directamente en host (menos reproducible), Nginx con gestión TLS manual.

## Consecuencias

Despliegue y rollback comprensibles. Requiere operación de host, volúmenes, backup, firewall y pruebas de restore. No convierte el monolito en microservicios.
