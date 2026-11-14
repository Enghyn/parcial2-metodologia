# Mockups — C-21 reportes

Política del proyecto: `system-and-mockups`, design system revisión 1 (aprobado 2026-11-04).

## Pantallas y estados

| # | Pantalla | Archivo | Descripción |
|---|----------|---------|-------------|
| 1 | Ocupación por sillón/profesional | `ocupacion.html` | Filtros de rango, selector profesional/sillón, tarjetas de ocupación por estado, tabla de detalle, export CSV |
| 2 | Facturación por medio de pago / OS | `facturacion.html` | Filtros de rango, tarjetas de totales por medio, desglose por OS, tabla, export CSV |
| 3 | Ausentismo y recuperación | `ausentismo.html` | Filtros de rango, tarjetas de cancelados/no presentados/recuperados, tasa de ausentismo, tabla, export CSV |
| 4 | Estado vacío / sin datos | (dentro de cada HTML) | Mensaje de estado vacío + CTA para ajustar el rango |
| 5 | Estados transversales | (dentro de cada HTML) | Carga, error de red, 403 por rol, rango inválido (422), éxito de export |

## Decisiones de diseño

- **Design system revision: 1**
- **Decision: yes** (project policy, system-and-mockups)
- **Mockups path:** `openspec/changes/c-21-reportes/mockups/`
- **Approval: approved (2026-11-14, by user)**
- **Preview: manual** (ver abajo)
- **Visual verify: pending**

Todos los mockups importan `design-system/tokens.css` y `design-system/brand.js`, usan solo assets locales y no crean tokens nuevos.

## Preview (renderizado manual)

Playwright MCP no está disponible en este entorno. Para inspeccionar visualmente:

1. Abrir cada HTML en un navegador moderno.
2. Redimensionar a **390×844** (mobile) y capturar.
3. Redimensionar a **1440×900** (desktop) y capturar.
4. Guardar capturas en `mockups/previews/` con nombres como `ocupacion-mobile-390x844.png`, `ocupacion-desktop-1440x900.png`, etc.
5. Inspeccionar cada pantalla y estado (carga, error, vacío, 403, éxito) en ambos tamaños.
6. Reportar defectos por prioridad (blocker / major / minor) al usuario.

## Approval

`Approval: approved (2026-11-14, by user)` — aprobado explícitamente por el usuario.

## Reemplazo de marca

El nombre de marca es `(marca provisoria)` definido en `design-system/brand.js`. Cambiar `BRAND_NAME` allí y volver a renderizar los previews si se define una marca final.
