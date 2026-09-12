# ADR 0016: Watchlist, Inspections, and File Storage

## Status
Accepted

## Context
Phase 6 (Watchlist e Inspección) requires tracking opportunities that move beyond automated scoring into manual review, physical inspection, and ultimately a purchase decision. This involves storing a watchlist, generating inspection checklists, and managing unstructured data such as photos or PDF reports from the inspection. We need a way to store these files securely outside of the database and webroot.

## Decisions

1. **Watchlist Identity**: La identidad de Watchlist debe colgar de `Opportunity` y conservar referencias a `listing`/`vehicle` sin duplicar su información. La tabla `watchlist` usará `opportunity_id` como clave primaria o foránea única.
2. **Pricing Snapshots**: El precio al guardar se persiste (snapshot); el precio actual y el histórico se derivan de snapshots posteriores.
3. **Deterministic Checklists**: El checklist de inspección se genera de forma determinista basándose en la configuración global y en los problemas conocidos del vehículo, y se congela al crear la inspección en la base de datos (copiando los items en lugar de referenciarlos dinámicamente).
4. **Knowledge Base Traceability**: Cada check específico conserva la referencia al `KnownIssue`/evidencia que lo originó, permitiendo trazabilidad y justificación.
5. **Local File Storage**: Los binarios (fotos, adjuntos) viven fuera de PostgreSQL y del webroot, detrás de un servicio o puerto dedicado `FileStorage`. Esto evita inflar la base de datos y protege los archivos de acceso no autenticado.
6. **State Transitions**: La transición del estado de una oportunidad a `PURCHASED` prepara la Fase 7, pero no crea aún la entidad `OwnedVehicle`.

## Consequences
- **Positive**: Clear separation of concerns between unstructured file storage and structured relational data. Deterministic checklists ensure historical audits are accurate even if the knowledge base changes.
- **Negative**: Managing a separate file storage directory requires extra backup and persistence configuration (e.g., Docker volumes) y un endpoint dedicado para servir archivos autenticados.
