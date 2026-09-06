# MotorScope

<div align="center">

![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16.3-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18.6-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-8.8-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Caddy](https://img.shields.io/badge/Caddy-2.10-22B573?style=for-the-badge&logo=caddy&logoColor=white)
![Security](https://img.shields.io/badge/Security-OWASP_ASVS_L2-blueviolet?style=for-the-badge)

**Plataforma privada de an�lisis, scoring determinista y gesti�n de oportunidades de veh�culos de ocasi�n.**

[Arquitectura](#-arquitectura) � [Puesta en Marcha](#-puesta-en-marcha) � [Calidad y Testing](#-calidad-y-testing) � [Seguridad](#-seguridad) � [Documentaci�n](#-documentaci�n)

</div>

---

## ?? Visi�n General

**MotorScope** es un sistema modular dise�ado para localizar, auditar y valorar oportunidades en el mercado de veh�culos de segunda mano. Construido con arquitectura de **Monolito Modular** y seguridad de grado empresarial (**OWASP ASVS Nivel 2**), prioriza la **calidad, auditabilidad y explicabilidad determinista** sobre algoritmos opacos.

El proyecto se rige por [`PLAN_MAESTRO_VEHICULOS_SEGUNDA_MANO.md`](PLAN_MAESTRO_VEHICULOS_SEGUNDA_MANO.md) y mantiene [`task.md`](task.md) como la fuente operativa de verdad de sus fases de desarrollo.

---

## ??? Estado del Proyecto

|  Fase   | Nombre                         |                                           Estado                                            | Criterios Clave                                                                          |
| :-----: | ------------------------------ | :-----------------------------------------------------------------------------------------: | ---------------------------------------------------------------------------------------- |
|  **0**  | **Inspecci�n y Planning**      |   ![Completada](https://img.shields.io/badge/Estado-Completada-success?style=flat-square)   | Inventario, arquitectura, modelo de datos, 11 ADRs iniciales y compliance de fuentes.    |
|  **1**  | **Foundation**                 |   ![Completada](https://img.shields.io/badge/Estado-Completada-success?style=flat-square)   | Monorepo, Auth (Argon2id, sesiones opacas, CSRF), UI accesible, Docker stack verificado. |
|  **2**  | **Search y Adquisici�n**       |   ![Completada](https://img.shields.io/badge/Estado-Completada-success?style=flat-square)   | Conectores Mock/Manual, `SearchFilter`, normalizaci�n, ingesta idempotente, snapshots, worker Dramatiq y frontend de exploraci�n y alta manual. |
| **3�9** | **Market Data, Scoring & MVP** | ![Planificado](https://img.shields.io/badge/Estado-Planificado-lightgrey?style=flat-square) | Opportunity Score determinista, Wiki automotriz, Inspecci�n, Garage y Hardening.         |

---

## ??? Arquitectura del Sistema

El sistema implementa un monolito modular con separaci�n estricta de dominios de negocio y topolog�a de red aislada:

```text
                               +-----------------------------+
                               �       Cliente Web / UI      �
                               �   (Navegador / Dispositivo) �
                               +-----------------------------+
                                              � HTTP/S (:3080 / :443)
                                              ?
+-----------------------------------------------------------------------------+
�  REVERSE PROXY (Caddy 2.10)                                                  �
�  - Terminaci�n TLS & Cabeceras de Seguridad (CSP, HSTS, X-Frame-Options)    �
�  - Enrutamiento unificado / y /api/*                                         �
+-----------------------------------------------------------------------------+
                        � /                           � /api/*
                        ?                             ?
+-------------------------------+     +---------------------------------------+
�  FRONTEND (Next.js 16)        �     �  BACKEND API (FastAPI 0.115)          �
�  - App Router & Server Comp.  �     �  - Dominios: auth, audit, users       �
�  - TanStack React Query       �     �  - Request ID & Logs JSON RFC 7807    �
�  - Tailwind CSS + Lucide      �     �  - Rate Limiter por sliding window    �
+-------------------------------+     +---------------------------------------+
                                                      �
                       +-----------------------------------------------------+
                       �                                                     �
                       ?                                                     ?
+---------------------------------------+     +---------------------------------------+
�  PERSISTENCIA RELACIONAL              �     �  MEMORIA & COLAS                      �
�  PostgreSQL 18 (Alpine)               �     �  Redis 8.8 (Alpine) + Dramatiq Worker �
�  - Esquema versionado con Alembic     �     �  - Rate limiting & invalidaci�n       �
�  - Red interna aislada (no expuesta)  �     �  - Tareas as�ncronas en background    �
+---------------------------------------+     +---------------------------------------+
```

### Estructura del Monorepo

```text
/
+-- apps/
�   +-- api/             # Backend FastAPI, Alembic, dominios funcionales y worker Dramatiq
�   +-- web/             # Frontend Next.js 16 App Router con dise�o accesible
+-- packages/
�   +-- shared/          # Contratos y tipos TypeScript compartidos
+-- infrastructure/
�   +-- docker/          # Dockerfiles multi-stage y optimizados (no-root)
�   +-- caddy/           # Caddyfile con enrutamiento y proxy inverso
�   +-- scripts/         # Herramientas de exportaci�n OpenAPI y shims multiplataforma
+-- docs/                # Arquitectura, ADRs, Modelo de Datos, ASVS, Testing y Operaciones
+-- docker-compose.yml   # Definici�n integral del stack de contenedores
+-- task.md              # Fuente operativa de verdad por tareas
+-- implementation_plan.md # Plan de ejecuci�n t�cnico y matriz de riesgos
```

---

## ?? Stack Tecnol�gico y Versiones

Versiones estables fijadas seg�n la pol�tica estricta de dependencias ([ADR-0011](docs/adr/0011-tooling-and-runtime-versions.md)):

- **Runtime Backend:** Python `3.14.7` gestionado con [`uv`](https://github.com/astral-sh/uv) `0.10.2`.
- **Framework API:** [FastAPI](https://fastapi.tiangolo.com/) `0.115.11` + [Uvicorn](https://www.uvicorn.org/) `0.34.0`.
- **ORM & Migraciones:** [SQLAlchemy](https://www.sqlalchemy.org/) `2.0.38` (async/sync estricto) + [Alembic](https://alembic.sqlalchemy.org/) `1.15.1`.
- **Base de Datos:** [PostgreSQL](https://www.postgresql.org/) `18.6` (Alpine multi-stage).
- **Cach� & Workers:** [Redis](https://redis.io/) `8.8.2` (Alpine) + [Dramatiq](https://dramatiq.io/) `1.17.1`.
- **Runtime Frontend:** Node.js `24.20.0 LTS` gestionado con [`pnpm`](https://pnpm.io/) `11.1.3`.
- **Framework Web:** [Next.js](https://nextjs.org/) `16.3.4` (App Router) + [React](https://react.dev/) `19.2.8`.
- **Tipado & Estilos:** TypeScript `5.9.3` (`strict: true`) + [Tailwind CSS](https://tailwindcss.com/) `4.3.3`.
- **Testing:** [Pytest](https://pytest.org/) `9.1.1` + [Vitest](https://vitest.dev/) `5.0.0` con `@vitest/coverage-v8` y `vitest-axe`.

---

## ?? Puesta en Marcha

### 1. Despliegue con Docker Compose (Recomendado)

El entorno incluye soporte directo para servidores Linux, VPS y despliegues en **Synology NAS (Container Manager)**:

```bash
# 1. Clonar el repositorio
git clone https://github.com/Zambudio/Compra-Venta-Autos.git
cd Compra-Venta-Autos

# 2. Configurar variables de entorno seguras
cp .env.example .env
# Generar claves aleatorias seguras en .env antes de iniciar

# 3. Construir y levantar servicios
docker compose up -d --build

# 4. Aplicar migraciones iniciales en PostgreSQL
docker compose exec api alembic upgrade head

# 5. Inicializar la cuenta OWNER administrativa
docker compose exec api python -m app.auth.cli create-owner
```

> **Nota para Synology NAS:** Caddy publica de manera predeterminada en el puerto host **`3080`** (HTTP) para evitar colisiones con el Nginx interno de Synology DSM. Ver [`Guia_Conexion_ssh_NAS.md`](Guia_Conexion_ssh_NAS.md) para m�s detalles.

### 2. Acceso a la Plataforma

Una vez levantado el stack, accede desde tu navegador:

- **Portal Web:** `http://localhost:3080` (o `http://<IP-HOST>:3080`)
- **API Health Liveness:** `http://localhost:3080/api/v1/health/live`
- **API Health Readiness:** `http://localhost:3080/api/v1/health/ready`
- **Documentaci�n Swagger OpenAPI:** `http://localhost:3080/docs`

---

## ?? Calidad y Testing

El repositorio cuenta con una cobertura global superior al **80%** y verificaciones autom�ticas de tipado estricto y linting:

### Backend (`apps/api`)

```powershell
# Formato y Linting
uv run ruff format --check .
uv run ruff check .

# Verificaci�n de Tipos Estricta
uv run mypy --strict .

# Suite de Pruebas con Cobertura (32 unit tests)
uv run pytest -m "not integration" --cov=src --cov-fail-under=80
```

### Frontend (`apps/web`)

```powershell
# Formato y Linting
pnpm format:check
pnpm --filter @motorscope/web lint

# Verificaci�n de Tipos
pnpm --filter @motorscope/web typecheck

# Suite de Pruebas Unitarias y Accesibilidad (15 tests con axe)
pnpm --filter @motorscope/web test

# Compilaci�n de Producci�n
pnpm --filter @motorscope/web build
```

---

## ?? Seguridad

MotorScope adopta un modelo de seguridad por dise�o alineado con **OWASP ASVS Nivel 2**:

- **Acceso Privado Denegado por Defecto:** Toda la superficie operativa exige autenticaci�n y rol expl�cito (`OWNER`, `VIEWER`).
- **Autenticaci�n Fuerte:** Contrase�as hasheadas con algoritmo **Argon2id** con par�metros recomendados por OWASP.
- **Sesiones Opacas Servidor:** Tokens de alta entrop�a (256 bits) almacenados en PostgreSQL y revocables inmediatamente.
- **Cookies Blindadas:** Atributos obligatorios `HttpOnly`, `SameSite=Lax` y `Secure` (en staging/producci�n).
- **Protecci�n CSRF:** Emparejamiento obligatorio de token en cabecera `X-CSRF-Token` para operaciones de mutaci�n.
- **Defensa Activa:** Rate limiting por IP/cuenta mediante sliding window en Redis (m�x. 5 intentos cada 15 min).
- **Auditor�a Inmutable:** Registro estructurado de eventos de seguridad (`LOGIN_SUCCESS`, `LOGIN_FAILURE`, `LOGOUT`) en la tabla `audit_events`.

Para reportar incidencias o consultar la pol�tica de seguridad, revisa [`SECURITY.md`](SECURITY.md) y [`docs/security/`](docs/security/).

---

## ?? Documentaci�n T�cnica

La documentaci�n completa del proyecto est� versionada en el directorio [`docs/`](docs/):

- **Arquitectura:** [`docs/architecture/architecture.md`](docs/architecture/architecture.md) y [`docs/architecture/data-flow.md`](docs/architecture/data-flow.md).
- **Modelo de Dominio:** [`docs/domain/data-model.md`](docs/domain/data-model.md).
- **Decisiones de Arquitectura (ADRs):** [`docs/adr/`](docs/adr/) (11 registros completos).
- **Contrato OpenAPI:** [`docs/api/openapi.json`](docs/api/openapi.json).
- **Estrategia de Pruebas:** [`docs/testing/testing-strategy.md`](docs/testing/testing-strategy.md).
- **Compliance y Fuentes Externas:** [`docs/source-compliance.md`](docs/source-compliance.md).
- **Operaciones y Despliegue:** [`docs/operations/deployment.md`](docs/operations/deployment.md) y [`docs/operations/backup-restore.md`](docs/operations/backup-restore.md).

---

## ?? Licencia

Este proyecto es software privado de uso exclusivo. Prohibida su distribuci�n o copia sin autorizaci�n expresa.
