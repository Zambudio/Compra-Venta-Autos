# OWASP ASVS 5.0 Level 2 — matriz inicial

Fecha de evaluación: 2026-09-06. Esta matriz no afirma certificación; registra el control y la evidencia esperada. `Planificado` no equivale a verificado.

| Área                      | Estado Foundation  | Control/evidencia                                                    |
| ------------------------- | ------------------ | -------------------------------------------------------------------- |
| V1 Codificación segura    | En implementación  | linters/tipos, DTOs, revisión, errores uniformes                     |
| V2 Validación y lógica    | En implementación  | Pydantic/Zod, límites de tamaño, constraints DB                      |
| V3 Web frontend           | En implementación  | React escaping, CSP, headers, no HTML no confiable                   |
| V4 API/Web services       | En implementación  | `/api/v1`, métodos/códigos, CORS, request ID, OpenAPI                |
| V5 Archivos               | Planificado Fase 7 | FileStorage, MIME por contenido, tamaño, fuera de webroot            |
| V6 Autenticación          | En implementación  | Argon2id, CLI owner, login uniforme, rate limit                      |
| V7 Sesión                 | En implementación  | token opaco, hash DB, cookies seguras, caducidad/revocación          |
| V8 Autorización           | En implementación  | default-deny y roles en backend                                      |
| V9 Tokens OAuth/OIDC      | No aplica          | no se usa OAuth/OIDC/JWT en Foundation                               |
| V10 Self-contained tokens | No aplica          | sesiones server-side, no JWT                                         |
| V11 Criptografía          | En implementación  | CSPRNG, Argon2id, compare_digest, TLS en borde                       |
| V12 Comunicación segura   | Parcial            | Caddy y HTTPS en remoto; TLS local opcional                          |
| V13 Configuración         | En implementación  | settings tipados, secretos fuera, fail-fast producción               |
| V14 Datos                 | Parcial            | PostgreSQL, minimización; política detallada antes de datos externos |
| V15 Diseño seguro         | En implementación  | ADRs, threat model, límites de confianza                             |
| V16 Logs y errores        | En implementación  | JSON, redacción, auditoría, errores sin trazas externas              |
| V17 WebSocket             | No aplica          | no hay WebSockets                                                    |

## Criterios verificables de Foundation

- Cookies de sesión: `HttpOnly`, `Secure` fuera de desarrollo local, `SameSite=Lax` (o más estricto si no rompe el flujo), path limitado y max-age.
- CSRF obligatorio en métodos inseguros autenticados; cookie y header coinciden y validan el hash de sesión.
- Hash Argon2id con librería mantenida; contraseña mínima de 12 y máxima de 128 caracteres.
- Rate limit de login atómico en Redis; fallo cerrado configurable en producción.
- CORS nunca usa wildcard con credenciales.
- Errores 500 no devuelven excepción/stack.
- DB/Redis no publican puertos; contenedores app sin root; imágenes por versión y digest.
- Ningún secreto, token, cookie, password o documento completo en logs/audit.

## Gates automáticos

Ruff, mypy, pytest, ESLint, TypeScript, Vitest, Playwright, Semgrep, Gitleaks, auditorías de dependencias, Trivy y CodeQL. La prueba de migración usa PostgreSQL real. Un HIGH/CRITICAL exige corrección o excepción con dueño, justificación, compensación y fecha de revisión.

## Pendientes antes de producción

Revisión manual completa requisito por requisito de ASVS 5.0 L2; TLS real; secretos gestionados; prueba DAST; recuperación/rotación operativa; retención/borrado/exportación; restore probado; revisión de archivos/SSRF cuando existan; canal de incidentes y propietarios nominales.
