# CLAUDE.md — MotorScope (Compra-Venta Autos)

Este archivo replica las instrucciones de [AGENTS.md](AGENTS.md) para Claude Code.

Plataforma inteligente de monitorización, análisis de mercado y detección de oportunidades de compra/venta de vehículos de segunda mano en España.

## Arquitectura y Monorepo

- **Monorepo**: pnpm workspaces + Turborepo.
  - `apps/web`: Frontend React 19 + Next.js 15 App Router + TailwindCSS + Shadcn/ui.
  - `apps/api`: Backend FastAPI (Python 3.12) con Clean Architecture modular (Auth, Vehicles, Market, Notifications).
  - `apps/worker`: Cola asíncrona Dramatiq respaldada por Redis para tareas de fondo.
  - `packages/scraper`: Scrapers modulares Playwright/Scrapy para portales españoles.
  - `packages/types`: Tipos TypeScript compartidos.
- **Base de Datos & Auth**: PostgreSQL 16 con TimescaleDB. Autenticación con sesiones opacas en Redis + hashing de contraseñas con Argon2id.
- **Motor de Oportunidades**: Algoritmo de scoring compuesto 0-100 (precio relativo de mercado, depreciación histórica, kilometraje anualizado y liquidez).

## Comandos Clave de Desarrollo

```bash
# Frontend & Monorepo
pnpm install
pnpm dev

# Backend (apps/api)
poetry install
poetry run uvicorn app.main:app --reload

# Tests & Calidad
pnpm test
pnpm lint
poetry run pytest
poetry run ruff check .
```

---

## 🧠 Base de Conocimiento Global (OBSIDIAN VAULT)

Este proyecto está formalmente integrado con nuestra base de conocimiento general para todos los proyectos:
📁 **`z:\IA\02_Proyectos\OBSIDIAN VAULT`**

### Reglas Obligatorias para Cualquier Agente de IA:
1. **Consulta Previa Obligatoria al Desarrollar**: Siempre que estemos desarrollando nuevas características, diseñando endpoints, algoritmos de scoring, colas de trabajo o integraciones, **el agente DEBE buscar y consultar información primero en `OBSIDIAN VAULT`** (`OBSIDIAN VAULT/index.md`).
   - Ficha de entidad: `Entities/Proyecto-MotorScope.md`.
   - Conceptos clave: `Concepts/Patron-Monolito-Modular-FastAPI.md`, `Concepts/Autenticacion-Sesiones-Opacas-Argon2id.md`, `Concepts/Arquitectura-Jobs-Asincronos-Dramatiq-Redis.md`, `Concepts/Modelo-Valoracion-Scoring-Oportunidades.md`, `Concepts/Integracion-Supabase-PgBouncer-FastAPI.md` y `Entities/Infraestructura-NAS-Synology-DS224.md`.
2. **Referencias cruzadas**: Si el usuario pide *"Hazlo como en el proyecto X"*, consulta las entidades y conceptos en `OBSIDIAN VAULT` para identificar las convenciones aprobadas en ese desarrollo.
3. **Reutilización y Consistencia**: No reinventes soluciones para autenticación, gestión de tareas asíncronas o integración con el NAS Synology; reutiliza los patrones documentados en la Vault.
4. **Documentar y Relacionar Obligatoriamente Nuevos Desarrollos e Implementaciones**:
   - Si durante el desarrollo de MotorScope se diseña una nueva implementación relevante, algoritmo, caso de uso, ADR o configuración de infraestructura:
   - **DEBE documentarse e interrelacionarse de inmediato en `OBSIDIAN VAULT`**.
   - Seguir la metodología Wiki-Base (`OBSIDIAN VAULT/SCHEMA.md`):
     - Depositar fuentes originales inmutables en `RAW/` si corresponde.
     - Redactar o actualizar fichas en `Entities/` o `Concepts/` cumpliendo el contrato normativo (frontmatter YAML con `tags`, `updated: YYYY-MM-DD`, `fuentes`).
     - Sección `## Cross-references` con Wikilinks nativos `[[...]]`, enlazando a las notas relevantes y SIEMPRE a `[[index]]`, `[[SCHEMA]]` y `[[log]]`.
     - Sección `## Fuentes`.
     - Respetar la regla de Vault cerrado (enlaces de navegación únicamente internos al Vault; rutas del proyecto como texto plano en backticks).
     - Actualizar obligatoriamente `OBSIDIAN VAULT/index.md` y añadir la entrada correspondiente en `OBSIDIAN VAULT/log.md`.
5. **Criterio de Síntesis**: Evita registrar código efímero o detalles de implementación menores; enfócate en decisiones arquitectónicas y patrones transferibles.
