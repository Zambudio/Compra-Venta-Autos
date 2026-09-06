# Política de seguridad

## Objetivo

El objetivo del proyecto es OWASP ASVS 5.0 Level 2. La aplicación es privada, aplica denegación por defecto y no acepta vulnerabilidades HIGH o CRITICAL sin corrección o excepción formal con propietario y fecha de revisión.

## Reporte responsable

No abras issues públicos con secretos, datos personales o detalles explotables. Hasta definir un canal privado del repositorio remoto, comunica el hallazgo directamente al propietario del proyecto por un medio privado acordado. No pruebes contra sistemas o cuentas de terceros sin autorización.

Incluye: versión/commit, entorno, pasos mínimos, impacto, evidencia saneada y mitigación sugerida. Nunca incluyas contraseñas, cookies, tokens, documentos completos, teléfonos o matrículas reales.

## Controles base

- contraseñas Argon2id y sesiones opacas revocables; el token solo viaja en cookie HttpOnly;
- CSRF en mutaciones autenticadas y SameSite apropiado;
- roles `OWNER`, `ADMIN`, `VIEWER`, autorizados siempre en backend;
- validación Pydantic/Zod, consultas ORM parametrizadas y DTOs de salida;
- CORS restrictivo, CSP y cabeceras de seguridad;
- rate limiting para login y operaciones sensibles;
- secretos exclusivamente mediante entorno/secret manager;
- logs estructurados con redacción y errores externos sin detalles internos;
- PostgreSQL/Redis sin exposición pública; TLS obligatorio en remoto;
- imágenes/dependencias fijadas y escaneadas en CI.

## Secretos

`.env` y variantes locales están ignorados. `.env.example` contiene nombres y valores deliberadamente inválidos, nunca credenciales operativas. Ante una filtración: revocar, rotar, revisar logs/auditoría, evaluar alcance y documentar el incidente.

## Soporte y actualizaciones

Dependabot mantiene dependencias y GitHub Actions. Las actualizaciones se validan con lockfiles, suites de tests, auditoría de dependencias y escaneo de imágenes antes de merge.

## Alcance conocido

Foundation no incluye recuperación de cuenta, MFA ni subida de archivos. No se deben habilitar hasta que exista diseño seguro, threat-model actualizado y pruebas específicas. El canal privado de reporte y el proceso formal de incidentes requieren concretarse antes de producción.
