# Especificación visual — Foundation Auth

Concepto: `foundation-auth-concept.png` (1536×1024), generado el 2026-09-06 como especificación interna. No es un asset de producción ni debe mostrarse como UI.

## Copy lock

Login: `MotorScope`, `Acceso privado`, `Gestiona tus oportunidades de vehículos con criterio y trazabilidad.`, `Correo electrónico`, `Contraseña`, `Entrar`, `Sesión segura y privada`.

Estado autenticado: `MotorScope`, `Estado`, `Cerrar sesión`, `Foundation operativa`, `API`, `PostgreSQL`, `Redis`, `Disponible`, `Preparado`, `Las funciones de búsqueda se habilitarán en la siguiente fase.`

## Sistema visual extraído

- Fondo blanco real `#ffffff`; texto principal carbón `#101820`; secundario `#5f666d`.
- Acento azul petróleo `#004b70`; foco visible del mismo tono; éxito `#00866a`.
- Reglas/bordes gris cálido `#d7d9dc`; superficies casi planas; radio 8 px.
- Sans-serif contemporánea del sistema; H1 32/38 semibold, marca 28/32 bold, body 16/24, controles 15/22.
- Login desktop en dos columnas: imagen técnica/automotriz oscura al 28–30% y formulario abierto; en móvil se oculta la imagen y el formulario ocupa el ancho.
- Estado: header sereno y lista abierta con separadores, no grid de cards.

## Componentes y estados

`AppBrand`, `TextField`, `PasswordField`, `Button`, `SecurityNote`, `AppHeader`, `StatusList`, `StatusRow`. Estados focus, disabled/loading, error y success visibles; foco de 2 px; targets mínimos de 44 px; no depender solo del color (texto de estado siempre presente).

Iconos: candado y cerrar sesión, lineales de 20 px, stroke 1.75, `currentColor`. No hay más iconografía.

## Responsive y accesibilidad

Desktop de referencia 1536×1024. Verificar también 1440×900 y móvil 390×844. Labels persistentes, errores asociados, orden de tab natural, contraste AA, `prefers-reduced-motion`, sin overflow horizontal.

## Restricciones

No añadir métricas, búsqueda, vehículos, cards, badges decorativos, gradientes, claims ni navegación de fases futuras. Todo texto/control es HTML, nunca parte de una imagen. El visual automotriz es opcional; si no se genera como asset separado, usar un tratamiento CSS sobrio documentado como desviación en lugar de recortar el concepto.
