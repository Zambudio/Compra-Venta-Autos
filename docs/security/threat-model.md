# Threat model

Versión inicial: 2026-09-06. Método: límites de confianza + STRIDE. Objetivo: OWASP ASVS 5.0 L2.

## Activos

Credenciales y sesiones; datos personales del propietario/vendedores; matrículas/teléfonos/ubicaciones si se autorizan; documentos; datos financieros; evidencias y clasificaciones; perfiles/scores; histórico de anuncios; secretos de infraestructura; logs de auditoría.

## Actores y límites

- Usuario legítimo (`OWNER`, futuro `ADMIN`/`VIEWER`).
- Atacante remoto no autenticado o cuenta comprometida.
- Fuente externa maliciosa o comprometida.
- Dependencia/imagen comprometida.
- Operador con acceso al host o backup.
- Navegador → Caddy → web/API → PostgreSQL/Redis → worker → fuentes/almacenamiento.

## Amenazas prioritarias

| ID   | STRIDE | Escenario                              | Riesgo        | Controles Foundation                                                        | Validación              |
| ---- | ------ | -------------------------------------- | ------------- | --------------------------------------------------------------------------- | ----------------------- |
| T-01 | S      | Credential stuffing/brute force        | Alto          | Argon2id, mensaje uniforme, rate limit Redis, audit                         | tests login/rate limit  |
| T-02 | S/E    | Robo/fijación de sesión                | Alto          | token CSPRNG, hash DB, Secure/HttpOnly/SameSite, rotación y revocación      | tests cookies/logout    |
| T-03 | T      | CSRF sobre mutaciones                  | Alto          | double-submit vinculado a sesión y comparación constante                    | tests CSRF              |
| T-04 | E      | Bypass de roles                        | Alto          | dependencias backend default-deny, rol enum                                 | tests 401/403           |
| T-05 | I      | XSS/filtración en salida               | Alto          | React escaping, DTOs, CSP, sin HTML arbitrario                              | headers/component tests |
| T-06 | T/I    | SQL injection/mass assignment          | Alto          | Pydantic, ORM parametrizado, DTOs separados                                 | tests negativos/SAST    |
| T-07 | I      | Secretos o PII en logs/errores         | Alto          | redacción, logs de metadata, error genérico                                 | tests + review          |
| T-08 | D      | Abuso de API/jobs/fuentes              | Medio/alto    | límites, timeout, rate limit, reintentos acotados, aislamiento              | integración             |
| T-09 | T/I    | SSRF por URLs/imágenes                 | Alto (Fase 2) | provider allowlist, DNS/IP validation, egress; no implementado aún          | gate Fase 2             |
| T-10 | T/I    | Archivo malicioso/path traversal       | Alto (Fase 7) | FileStorage, MIME real, allowlist, UUID, fuera de webroot                   | gate Files              |
| T-11 | R      | Negación de acciones críticas          | Medio         | AuditEvent con actor/request/result y reloj UTC                             | integration tests       |
| T-12 | I/T    | Backup robado o corrupto               | Alto          | cifrado, copia off-site, mínimo acceso, restore probado                     | ejercicio Fase 8        |
| T-13 | T      | Supply chain                           | Alto          | lockfiles, pin de imágenes, Dependabot, audit/Semgrep/Gitleaks/Trivy/CodeQL | CI                      |
| T-14 | I      | Scraping/retención ilícita de terceros | Alto/legal    | Manual/Mock only, compliance review por fuente, minimización                | revisión previa         |

## Abuso de autenticación

No hay autorregistro ni endpoint de bootstrap público. El primer OWNER se crea por CLI dentro del entorno de confianza. Login no revela si el email existe; se ejecuta verificación equivalente con hash ficticio. La sesión caduca, puede revocarse y solo se persiste como hash. Logout requiere CSRF.

## Privacidad

Foundation solo necesita email del usuario. Datos de fuentes se posponen hasta tener finalidad, base, retención y minimización. Matrículas y teléfonos no se usarán como señal salvo revisión legal; imágenes/documentos no estarán públicamente accesibles. Exportación/borrado se diseña antes de incorporar esos datos.

## Riesgos residuales / pendientes

- Docker no está disponible en el host actual: falta validar topología y scans de imagen localmente.
- El canal formal de incidentes y responsables nominales se definen antes de staging.
- MFA y recuperación segura no pertenecen a Foundation; una cuenta comprometida conserva impacto alto.
- SSRF y archivos son amenazas futuras bloqueadas por gates de sus fases.

Revisar este modelo al añadir una fuente, un tipo de dato personal, archivos, notificaciones externas, recuperación de cuenta o cambios de despliegue.
