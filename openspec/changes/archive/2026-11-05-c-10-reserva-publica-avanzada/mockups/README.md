# Mockups — C-10 `reserva-publica-avanzada`

Mockups del portal público y la autogestión con token, creados **antes de aplicar** el change, según la política `system-and-mockups` del proyecto.

- **Change:** `openspec/changes/c-10-reserva-publica-avanzada`
- **Capacidades afectadas:** `public-reservation` (MODIFIED + ADDED), `agenda` (ADDED)
- **Sistema de diseño:** `design-system/` — **revisión 1**, `Approval: approved (2026-11-04, by user)`
- **Aprobación de estos mockups:** `approved (2026-11-05, by user)`
- **Fecha de creación:** 2026-11-05
- **Navegador de captura:** Chromium (Playwright MCP), `scale: css`

> La marca, el logo y los datos de ejemplo son **provisorios**. El nombre sale de `design-system/brand.js` (`[data-brand-name]`) y el logo de `design-system/assets/logo.svg`, que dice "LOGO PROVISORIO". Nada de esto debe presentarse como identidad final.

## Pantallas

| Archivo | Qué muestra |
|---|---|
| `reserva-publica.html` | Portal `/reservar`: pasos 2/3/4/5 — disponibilidad, datos, pre-reserva con countdown (normal/alerta/vencida), confirmación con QR colapsable. |
| `turno-publico.html` | `/p/turno/:token` con estados `reservado`/`confirmado`/`cancelado`, QR propio y modal de reprogramación. |
| `errores-publicos.html` | Catálogo de errores del portal: 409 conflicto, 409 retención vencida, 429 rate-limit, 404 token inválido, 422 validación. |

### `reserva-publica.html`
- Wizard de 5 pasos con barra de progreso.
- Paso 2: grilla de huecos (libre, ocupado, retenido con cuenta regresiva) y filtros profesional/prestación.
- Paso 3: formulario Nombre/DNI/Teléfono (R1 `extra='forbid'`).
- Paso 4: retención con countdown en 3 estados (normal ≥2 min, alerta <1 min, vencida).
- Paso 5: éxito con WhatsApp click-to-chat y bloque colapsable con QR del portal.
- QR generado en servidor (sin red externa).

### `turno-publico.html`
- Estado `reservado`: acciones Reprogramar/Cancelar + WhatsApp.
- Estado `confirmado`: reprogramación deshabilitada (ventana vencida).
- Estado `cancelado`: CTA para reservar otro turno.
- QR propio del turno.
- Modal de reprogramación con nuevo inicio y duración no editable (la define la prestación).

### `errores-publicos.html`
- 409 conflicto de agenda · 409 retención vencida/consumida · 429 con `Retry-After` · 404 token inválido/opaco · 422 validación.
- Cada estado explica qué pasó y qué hacer; códigos HTTP y códigos internos anotados.

## Capturas

Las capturas se guardan en `previews/` a 390×844 y 1440×900 (Chromium headless, `scale: css`), renderizadas el 2026-11-05. El agente no puede inspeccionar imágenes; se recomienda revisión visual manual.

## Aprobación

`Approval: pending` — pendiente de revisión visual por el usuario.
