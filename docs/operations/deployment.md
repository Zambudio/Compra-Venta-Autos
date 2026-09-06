# Despliegue

Estado: runbook inicial; no validado en staging. Fecha: 2026-09-06.

## Topología recomendada

VPS o plataforma simple con Docker Compose. Caddy es el único servicio público (80/443 o puerto configurable como 3080 en NAS), obtiene TLS o gestiona el proxy inverso interno y enruta `/api/*` a FastAPI y el resto a Next.js. PostgreSQL y Redis están únicamente en red interna y con volúmenes persistentes. Staging y producción usan hosts/proyectos, secretos y bases separados.

## Entorno Synology NAS (Verificado)

En despliegues sobre Synology NAS con Container Manager:

- **Binario Docker Compose:** `/volume1/@appstore/ContainerManager/usr/bin/docker-compose`.
- **Puertos:** Para evitar colisiones con el Nginx interno de Synology DSM (puertos 80, 443, 8000), Caddy se mapea externamente al puerto `3080` (HTTP) y `8443` (HTTPS) mediante variables `CADDY_HTTP_PORT` y `CADDY_HTTPS_PORT`.
- **Volumen PostgreSQL 18+:** El punto de montaje en el contenedor de PostgreSQL 18 debe ser `/var/lib/postgresql` (en lugar de `/var/lib/postgresql/data`).
- **Comandos operativos:** Consultar `Guia_Conexion_ssh_NAS.md`.

1. Fijar dominio, firewall (solo 22 restringido, 80/443), usuario operativo sin root y parches del host.
2. Instalar Docker/Compose soportados y verificar digests de imágenes.
3. Provisionar secret manager o archivos de entorno con permisos mínimos fuera del repo.
4. Configurar DNS, correo de alertas y directorios/volúmenes con propietario correcto.
5. Ejecutar backup previo y comprobar espacio.

## Despliegue

```text
git fetch --tags
git verify-tag <release>
docker compose pull
docker compose build --pull
docker compose run --rm api uv run alembic upgrade head
docker compose up -d --remove-orphans
docker compose ps
```

Validar liveness/readiness, login/logout, métricas, logs sin secretos y que 5432/6379 no sean accesibles desde Internet. No ejecutar migraciones manuales en producción.

## Rollback

Conservar imagen/manifest y release anterior. Ante fallo compatible con esquema, volver a las imágenes previas. Si el esquema no es compatible, detener escrituras y aplicar el downgrade revisado solo si es seguro; en otro caso restaurar en instancia nueva desde backup verificado. Documentar incidente y reconciliar datos antes de reabrir.

## Secretos y rotación

No se hornean en imágenes. Cambios de secreto requieren despliegue coordinado; credenciales DB/Redis y claves operativas se rotan con ventana de solapamiento cuando sea posible. Revocar sesiones si una clave/token relacionado se compromete.

## Recursos iniciales

Definir límites medidos; punto de partida para un VPS pequeño: API/worker/web con límites explícitos, PostgreSQL con volumen y memoria suficiente, Redis con `maxmemory`/política documentada. Ajustar tras métricas, no por intuición.

## Pendientes antes de producción

Elegir proveedor/dominio, ejecutar staging, Trivy/ZAP, prueba de migración/rollback, restore real, alertas, responsables y checklist de producción. Este documento no declara el despliegue validado.
