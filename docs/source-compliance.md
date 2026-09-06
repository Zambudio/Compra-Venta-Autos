# Compliance de fuentes externas

Revisión inicial: 2026-09-06. Esta tabla es un control técnico conservador, no asesoramiento legal. Cada integración automatizada exige una nueva revisión y autorización explícita antes de implementarse.

| Source      | AcquisitionMethod MVP                   |              AutomatedAllowed |                             AuthenticationRequired | RateLimit      | TermsURL                                          | CheckedAt  | Notes                                                                                                                                                                                                |
| ----------- | --------------------------------------- | ----------------------------: | -------------------------------------------------: | -------------- | ------------------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Wallapop    | importación manual/asistida             |                            No |                     Usuario para ciertas funciones | N/A            | https://about.wallapop.com/condiciones-de-uso/    | 2026-09-06 | Términos revisados 2026-04-10 prohíben extracción sistemática, robots, minería y bots sin autorización. `robots.txt` devolvió 403 durante la revisión.                                               |
| Coches.net  | importación manual/asistida             |                            No |               No para consulta manual; sí área pro | N/A            | https://www.coches.net/condiciones-de-uso/        | 2026-09-06 | Términos prohíben extracción por robots/scrapping/minería; `robots.txt` bloquea `/search/` y múltiples filtros. Existe widget iframe de desarrolladores, no una API de ingestión demostrada.         |
| AutoScout24 | importación manual/asistida             |                            No |                     Área dealer para profesionales | N/A            | https://www.autoscout24.es/empresa/agb/           | 2026-09-06 | §8.2 prohíbe consultas automatizadas mediante scripts; `robots.txt` bloquea endpoints/listas/APIs relevantes.                                                                                        |
| Milanuncios | importación manual/asistida             | No confirmado; tratar como No | No para consulta manual; profesional según volumen | N/A            | https://www.milanuncios.com/legal/condiciones-uso | 2026-09-06 | Términos accesibles pero contenido legal no se renderizó completo en la consulta; `robots.txt` bloquea `/api/` y parámetros/rutas de búsqueda. Se requiere permiso contractual antes de automatizar. |
| Mock        | fixture local versionada y anonimizada  |                            Sí |                                                 No | N/A            | N/A                                               | 2026-09-06 | Única fuente automática prevista para tests normales.                                                                                                                                                |
| Manual      | formulario/archivo aportado por usuario |        Sí, bajo acción humana |                                        App privada | límites de app | N/A                                               | 2026-09-06 | Validar procedencia, minimización, copyright, tamaño y contenido antes de persistir.                                                                                                                 |

## Reglas obligatorias

No eludir CAPTCHA, anti-bot, rate limits o autenticación; no rotar proxies para evadir controles; no suplantar dispositivos; no usar APIs privadas obtenidas por ingeniería inversa. `robots.txt` no sustituye a los términos ni concede por sí solo permiso.

## Proceso antes de habilitar un Provider

1. Revisar términos/privacidad/robots actuales y conservar URL/fecha/evidencia.
2. Buscar API o feed oficial y contactar canal profesional.
3. Definir finalidad, datos mínimos, retención, frecuencia y autenticación.
4. Aprobar legal/producto y threat model; documentar límites y rate limit.
5. Implementar provider sustituible, contrato y fixtures anonimizadas.
6. Probar sin portales reales en CI; monitorizar estado, latencia y errores.

## Situación actual

Fase 1 no implementa conectores ni acceso a portales. Fase 2 solo puede comenzar con `MockProvider` y `ManualProvider`. Los conectores nominales podrán existir como contrato/configuración deshabilitada, nunca como scraping.
