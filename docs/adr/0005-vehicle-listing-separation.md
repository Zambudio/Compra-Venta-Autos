# ADR-0005: separar Vehicle y Listing

- **Estado:** Aceptado
- **Fecha:** 2026-09-06

## Contexto

Un vehículo físico puede aparecer en varios anuncios/fuentes y cada anuncio tiene identidad e histórico propios.

## Decisión

`Vehicle` representa la unidad normalizada; `Listing` representa `(Source, external_id)`. La asociación puede ser tardía y varios listings apuntan a un vehicle.

## Alternativas

Una entidad única por anuncio; fusionar automáticamente por una única señal.

## Consecuencias

Históricos y deduplicación correctos, a costa de workflow de matching. Los matches inciertos se guardan como candidatos y requieren revisión humana.
