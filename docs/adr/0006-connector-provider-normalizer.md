# ADR-0006: Connector / Provider / Normalizer

- **Estado:** Aceptado
- **Fecha:** 2026-09-06

## Contexto

Los métodos y permisos de adquisición cambian por portal y en el tiempo. Acoplar dominio a HTML crea fragilidad y riesgo legal.

## Decisión

`SearchEngine → SourceConnector → DataProvider → Normalizer`. Connector traduce semántica de fuente; Provider encapsula API/feed/manual/browser autorizado; Normalizer produce esquema interno.

## Alternativas

Scrapers directos por caso de uso; un agregador externo único; HTML dentro de servicios de dominio.

## Consecuencias

Providers sustituibles y tests contractuales. Requiere compliance review antes de activar cada método. MVP empieza solo con Mock y Manual.
