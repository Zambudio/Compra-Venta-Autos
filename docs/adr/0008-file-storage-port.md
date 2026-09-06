# ADR-0008: almacenamiento local detrás de FileStorage

- **Estado:** Aceptado (diseño; implementación Fase 7)
- **Fecha:** 2026-09-06

## Contexto

Fotos, facturas y contratos requieren control de acceso; el MVP no justifica S3, pero debe poder migrar.

## Decisión

Puerto `FileStorage`; adaptador local fuera del webroot, claves aleatorias, MIME por contenido, allowlist, límites, hash e I/O autorizado.

## Alternativas

Guardar blobs en PostgreSQL; publicar un directorio; S3 desde el inicio.

## Consecuencias

Operación local simple y migración futura viable. Backup debe coordinar DB y archivos; las descargas siempre pasan por autorización de la API.
