# ADR-0010: Opportunity Score determinista y versionado

- **Estado:** Aceptado (diseño; implementación Fase 5)
- **Fecha:** 2026-09-06

## Contexto

Las decisiones de compra necesitan explicación, reproducibilidad y auditoría con pocos datos históricos.

## Decisión

Motor de reglas determinista. Pesos/configuración viven en `ScoringProfileVersion` inmutable; cada resultado persiste componentes, explicación, instante y versión.

## Alternativas

Pesos hardcoded; ML; LLM decisor; sobrescribir scores históricos.

## Consecuencias

Resultados explicables y reproducibles. Cambios requieren nueva versión y pruebas. No se presenta como certeza y se separan observación, cálculo, estimación e inferencia.
