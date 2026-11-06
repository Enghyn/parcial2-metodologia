# Mockups — C-11 `ficha-clinica-avanzada`

Mockups de la ficha clínica avanzada, creados **antes de aplicar** el change, según la política `system-and-mockups` del proyecto.

- **Change:** `openspec/changes/c-11-ficha-clinica-avanzada`
- **Capacidades afectadas:** `clinical-records` (MODIFIED), `core-data-model` (MODIFIED)
- **Sistema de diseño:** `design-system/` — **revisión 1**, `Approval: approved (2026-11-04, by user)`
- **Aprobación de estos mockups:** `approved (2026-11-05, by user)`
- **Fecha de creación:** 2026-11-05
- **Navegador de captura:** Chromium headless, `scale: css`

> La marca, el logo y los datos de ejemplo son **provisorios**. El nombre sale de `design-system/brand.js` y el logo de `design-system/assets/logo.svg`.

## Pantallas

| Archivo | Qué muestra |
|---|---|
| `ficha-clinica.html` | Shell de la ficha: header del paciente, tabs (Odontograma / Evolución / Consentimiento / Historial por pieza), odontograma FDI con panel de hallazgo, notas de evolución append-only, consentimientos versionados, timeline por pieza. |
| `estados-clinicos.html` | Vistas por rol (odontólogo/recepción/admin) y estados transversales: carga, vacío (×3), banners 401/403/404/409/422 y éxito. |

### `ficha-clinica.html`
- Header del paciente con avatar, nombre, DNI, edad, última visita.
- Tabs para las 4 secciones.
- Odontograma FDI con 8 piezas de ejemplo y panel de hallazgo (estado, observación, último cambio, autor).
- Evolución clínica: lista cronológica con autor/fecha + formulario de nueva nota (solo odontólogo).
- Consentimiento informado: versiones v1/v2 con badge Vigente/Histórico + alta de nueva versión.
- Historial por pieza: timeline con transiciones estado_anterior → estado_nuevo, autor y fecha.

### `estados-clinicos.html`
- 3 roles con permisos descritos (R8: RBAC en backend, UI solo oculta/deshabilita).
- Carga (skeleton), vacío (×3), banners 401/403/404/409/422 y éxito.
- Nota R9: datos clínicos nunca en logs ni URLs.

## Capturas
Las capturas se guardan en `previews/` a 390×844 y 1440×900 (Chromium headless, `scale: css`), renderizadas el 2026-11-05.

## Aprobación
`Approval: pending` — pendiente de revisión visual por el usuario.
