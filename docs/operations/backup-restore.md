# Backup y restore

Estado: política inicial; restore aún no probado. Fecha: 2026-09-06.

## Objetivos

- RPO inicial propuesto: 24 horas para datos de negocio; revisar al crecer el volumen.
- RTO inicial propuesto: 4 horas.
- Retención propuesta: 7 diarios, 4 semanales y 12 mensuales, sujeta a privacidad/coste.

Estas cifras requieren aprobación operativa antes de producción.

## Alcance

PostgreSQL, almacenamiento de archivos, configuración no secreta y material necesario para restaurar. Redis es efímero y no es fuente de verdad. Los secretos se respaldan mediante el mecanismo del proveedor, nunca dentro del dump del proyecto.

## Backup

1. `pg_dump` en formato custom desde una cuenta de backup de mínimo privilegio.
2. Inventario/hash de adjuntos y backup consistente del storage.
3. Cifrado autenticado antes de salir del host.
4. Copia en almacenamiento independiente/off-site con versionado/inmutabilidad cuando exista.
5. Registro de timestamp, versión PostgreSQL/app, tamaño, checksum y resultado.
6. Alertar fallos y probar lectura/checksum automáticamente.

## Restore probado

Mensualmente y antes de releases de riesgo:

1. Crear entorno aislado y vacío con versiones compatibles.
2. Descargar, descifrar y verificar checksum.
3. Restaurar PostgreSQL y archivos; ejecutar migraciones si corresponde.
4. Validar constraints, conteos esperados, hashes de muestra, readiness y smoke tests.
5. Medir RPO/RTO real, registrar evidencia y destruir de forma segura el entorno de ensayo.

Un backup sin restore exitoso reciente se considera no válido.

## Responsabilidad y seguridad

Responsable nominal: pendiente de asignación antes de staging. Acceso bajo mínimo privilegio y MFA del proveedor; logs sin contenido de documentos. Borrados/retención legales deben propagarse a backups según capacidad y política documentada.

## Recuperación de desastre

Provisionar host nuevo, restaurar secretos por canal seguro, desplegar release compatible, restaurar DB/storage, validar internamente y cambiar tráfico solo tras smoke tests. Conservar el entorno afectado para investigación cuando sea legal y seguro.
