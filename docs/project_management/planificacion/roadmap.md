# Roadmap

Última actualización: 2026-09-13. **Proyecto aparcado**; ver
[`INFORME_ESTADO_Y_RELEVO_2026-09-13.md`](../informes_cierre/INFORME_ESTADO_Y_RELEVO_2026-09-13.md)
para el estado verificado, riesgos abiertos (incluye uno de cumplimiento legal sobre
Wallapop) y los próximos pasos priorizados.

## MVP

Objetivo: completar con calidad el flujo privado de una operación real, con adquisición legal y decisiones explicables.

1. ✅ Foundation segura y operable: auth, observabilidad, PostgreSQL, Redis, jobs, CI y entorno reproducible.
2. ✅ Búsqueda mediante conectores `Manual` y `Wallapop` (real, con gestión dinámica de estado); `Mock` retirado en Fase 10. **Ver riesgo de cumplimiento legal en el informe de relevo antes de asumir que Wallapop está autorizado.**
3. ✅ Normalización, separación `Vehicle`/`Listing`, snapshots y deduplicación asistida.
4. ✅ Wiki técnica con fuentes y evidencias; clasificación basada en datos.
5. ✅ Score determinista/versionado, comparables, intervalos, confianza y mesa de oportunidades.
6. ✅ Watchlist e inspección con checklist trazable y adjuntos seguros. Sin tests frontend (deuda conocida).
7. ✅ Compra, ledger de gastos append-only, venta, beneficio y ROI real. Sin tests frontend (deuda conocida).
8. ⚠️ Hardening ASVS 5.0 L2, accesibilidad, rendimiento, backup/restore y release reproducible — autodeclarado completo pero sin evidencia verificable; tratar como pendiente real.

Estado global: Fases 0–7 y 10–10.1 implementadas y verificadas hoy; Fase 8/9 sin
verificación real. El plan ejecutable en `task.md` e `implementation_plan.md` no
está sincronizado más allá de Fase 5; no son fuente de verdad hasta que se
actualicen (ver informe de relevo).

Restricciones: una sola aplicación backend, una base PostgreSQL, sin automatización de portales no autorizada, sin IA decisora y sin funcionalidades V2/V3.

## V2

- Integraciones o feeds oficiales autorizados y nuevos `Provider` sin cambiar contratos del dominio.
- Notificaciones externas por correo/push mediante el puerto existente.
- Almacenamiento S3-compatible detrás de `FileStorage`.
- Mejoras de deduplicación por perceptual hash y revisión asistida.
- Gestión multiusuario avanzada, invitaciones y recuperación de cuenta segura.
- Informes y análisis históricos más ricos, conservando explicabilidad.

## V3

- Escalado operacional a más vehículos y mayor volumen, solo si las métricas lo justifican.
- Extracción selectiva de módulos a servicios únicamente ante evidencia de necesidad.
- Asistencia de IA para resumir y organizar evidencias, nunca para decidir automáticamente ni perder trazabilidad.
- Modelos estadísticos/ML solo tras disponer de datos suficientes, evaluación formal, explicabilidad y ADR.

## Criterio de promoción

Una capacidad pasa a la siguiente versión solo tras completar el MVP, demostrar necesidad, actualizar riesgos/privacidad y aprobar el ADR cuando afecte a arquitectura, alcance o riesgo.
