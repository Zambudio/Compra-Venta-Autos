# ADR-0007: autenticación con sesiones opacas server-side

- **Estado:** Aceptado
- **Fecha:** 2026-09-06

## Contexto

La aplicación privada necesita revocación inmediata, cookies seguras, CSRF y pocos usuarios. No necesita federación ni tokens portables.

## Decisión

Contraseñas Argon2id; token de sesión aleatorio de 256 bits, solo hash SHA-256 en PostgreSQL; cookie HttpOnly/Secure/SameSite; CSRF double-submit vinculado por hash; roles backend y rate limit Redis. OWNER inicial por CLI, sin autorregistro.

## Alternativas

JWT en localStorage (rechazado por XSS y revocación), JWT en cookie (más complejidad sin beneficio), proveedor OIDC externo (posible futuro), Basic Auth.

## Consecuencias

Revocación y auditoría simples. Cada petición autenticada consulta persistencia; se podrá cachear con cuidado si se demuestra necesidad. Recuperación/MFA se posponen hasta diseñarlas con seguridad.
