# Sistema de diseño — Consultorio odontológico

Fundación visual portable del proyecto. **No es una marca final**: el nombre, el
logo y las imágenes siguen pendientes de definición y se muestran como `(TBD)`.

- **Mode:** `system-and-mockups`
- **Revision:** `1`
- **Approval:** `approved (2026-11-04, by user)`
- **Date:** 2026-11-04
- **Owned by:** skill `design-system`
- **Sources:** `frontend/src/index.css`, `frontend/src/features/agenda/*`,
  `frontend/src/features/caja/CajaPage.tsx`,
  `frontend/src/features/clinica/PacientesPage.tsx`,
  `frontend/src/features/reserva-publica/ReservarWizard.tsx`,
  `frontend/src/app/layout.tsx`, `knowledge-base/01`, `knowledge-base/03`,
  `knowledge-base/06`, `knowledge-base/08`, `AGENTS.md` (detalle en “Fuentes
  auditadas”).
- **Scope:** solo la fundación compartida. Los mockups de cada cambio visual viven
  en `openspec/changes/<name>/mockups/` y reutilizan esta revisión.

> El estado de la política (`visual_design`) lo escribe el orquestador en
> `.active-orchestrator-state.json` después de la aprobación del usuario. Esta
> fundación no modifica ese archivo.

## Para qué sirve

Una única fuente de valores visuales para que el frontend existente (React +
Tailwind v4), los mockups HTML y futuras pantallas compartan color, tipografía,
espaciado, radios, sombras, foco y movimiento. Es deliberadamente dependency-free:
no requiere Figma, build, cuenta paga, fuente remota ni herramienta exclusiva de
un agente.

## Fuentes auditadas

Se preservó la identidad existente; no se rebrandeó nada.

| Fuente | Qué se tomó |
|---|---|
| `frontend/src/index.css` | Tokens base: background, foreground, border, primary, primary-foreground |
| `frontend/src/features/agenda/estadoColor.ts` | Tríos de color de los 6 estados de turno |
| `frontend/src/features/agenda/TurnoCard.tsx` | Card densa: radio, borde, jerarquía, acciones micro |
| `frontend/src/features/agenda/EstadoTurnoMenu.tsx` | Botones de acción pequeños en mayúscula |
| `frontend/src/features/agenda/AgendaColumn.tsx` | Columna por sillón, borde y header |
| `frontend/src/features/agenda/TurnoModal.tsx` | Shell de modal, labels, inputs, botones |
| `frontend/src/features/agenda/ReprogramarModal.tsx` | Modal `max-w-md`, formulario y acciones |
| `frontend/src/features/agenda/AgendaPage.tsx` | Cabecera de página, CTA primario, grilla de sillones |
| `frontend/src/features/caja/CajaPage.tsx` | Tabla, métricas, alerta de seña, montos ARS |
| `frontend/src/features/clinica/PacientesPage.tsx` | Búsqueda, alta y patrón de formulario |
| `frontend/src/features/reserva-publica/ReservarWizard.tsx` | Superficie pública, alertas y ancho de lectura |
| `frontend/src/app/layout.tsx` | Topbar, navegación y layout privado/público |
| `knowledge-base/01_vision_y_objetivos.md` | Propósito, audiencia y alcance |
| `knowledge-base/03_actores_y_roles.md` | Roles y superficies pública/privada |
| `knowledge-base/06_funcionalidades.md` | US-001: datos que debe mostrar un turno |
| `knowledge-base/08_arquitectura_propuesta.md` | Estructura de features y stack |
| `AGENTS.md` | R10 (español rioplatense, ARS) y reglas duras |

También se cargó la skill `emil-design-eng` como guía de pulido (foco, presión de
botones, movimiento reducido). Los tokens existentes prevalecen ante cualquier
conflicto.

## Archivos

| Archivo | Rol |
|---|---|
| `README.md` | Política, revisión, fuentes, reemplazos y preview |
| `brand.md` | Nombre, tono, reglas de logo, imágenes y microcopy |
| `brand.js` | Único valor de nombre + binding de `[data-brand-name]` |
| `tokens.css` | Todos los valores visuales (color, tipo, espacio, radio, sombra, foco, movimiento) |
| `components.html` | Referencia visual de componentes y estados |
| `assets/logo.svg` | Logo provisorio, visiblemente marcado |
| `previews/` | Capturas 390×844 y 1440×900 |

## Mapa de tokens heredados

| Origen | Token nuevo | Valor |
|---|---|---|
| `index.css` → `--color-background` | `--color-background` / `--color-surface` | `oklch(1 0 0)` |
| `index.css` → `--color-foreground` | `--color-foreground` / `--color-text` | `oklch(0.25 0.02 260)` |
| `index.css` → `--color-border` | `--color-border` | `oklch(0.9 0.01 260)` |
| `index.css` → `--color-primary` | `--color-primary` | `oklch(0.55 0.15 240)` (hue intacto) |
| `index.css` → `--color-primary-foreground` | `--color-primary-foreground` / `--color-on-primary` | `oklch(1 0 0)` |
| `estadoColor.ts` → `sky-300 / sky-50 / sky-900` | `--state-reservado-{border,bg,text}` | equivalente |
| `estadoColor.ts` → `blue-400 / blue-50 / blue-900` | `--state-confirmado-{border,bg,text}` | equivalente |
| `estadoColor.ts` → `amber-400 / amber-50 / amber-900` | `--state-presente-{border,bg,text}` | equivalente |
| `estadoColor.ts` → `emerald-400 / emerald-50 / emerald-900` | `--state-atendido-{border,bg,text}` | equivalente |
| `estadoColor.ts` → `rose-300 / rose-50 / rose-900` | `--state-cancelado-{border,bg,text}` | equivalente |
| `estadoColor.ts` → `slate-400 / slate-100 / slate-700` | `--state-ausente-{border,bg,text}` | equivalente |
| No existía | `--state-sobreturno-{border,bg,text}` | neutral + borde discontinuo (derivado) |

Valores derivados para completar la fundación (hover, superficies, texto
secundario, semánticos, espaciado, radios, sombras, foco y movimiento) están
comentados como tales en `tokens.css`.

## Cómo previsualizar

1. Abrir directamente
   `C:\Users\enzon\OneDrive\Escritorio\active-or-practica\design-system\components.html`
   en un navegador actualizado.
2. Si el navegador bloquea assets locales, servir la carpeta:

   ```powershell
   python -m http.server 8765 --directory design-system
   ```

   y abrir `http://localhost:8765/components.html`. Detener el servidor con
   `Ctrl+C`.

No hay build, red, fuentes remotas ni dependencias. `brand.js` funciona sin
servidor y tiene fallback de texto si JavaScript está deshabilitado.

## Aprobación

- La fundación se entrega con `Approval: pending`.
- El usuario debe revisar `components.html` y las capturas de `previews/`.
- Con aprobación explícita, cambiar a
  `Approval: approved (AAAA-MM-DD, by user)` y mantener `Revision: 1`.
- Si se pide una revisión, dejar `Approval: pending`, ajustar y volver a mostrar
  los previews.
- Cualquier cambio de token o asset compartido sube `Revision:` a `2`, vuelve
  `Approval: pending`, obliga a re-renderizar los previews y a identificar los
  mockups afectados.

## Reemplazos exactos (TBD)

1. **Nombre de marca**
   - Editar solo `BRAND_NAME` en `brand.js`.
   - No tocar los HTML: todos leen `[data-brand-name]`.
   - Reemplazar la etiqueta visible `(marca provisoria)` y el marcador `(TBD)`
     del banner de `components.html` cuando exista un nombre aprobado.
2. **Logo**
   - Reemplazar `assets/logo.svg` por el logo aprobado, conservando el nombre y
     la ruta del archivo.
   - Actualizar el `alt` de las imágenes en `components.html` si cambia el
     significado.
3. **Valores visuales**
   - Editar los tokens en `tokens.css`. No introducir colores literales en los
     componentes.
   - Si cambia el primario, revisar contraste de `--color-on-primary`.
4. **Imágenes**
   - Agregar assets locales en `assets/` y referenciarlos con rutas relativas.
     No usar CDN ni stock.
5. **Cierre del reemplazo**
   - Subir `Revision:` y volver `Approval: pending` en este README.
   - Re-renderizar `components-390x844.png` y `components-1440x900.png`.
   - Volver a pedir aprobación explícita.

## Decisiones abiertas (TBD)

- **Nombre de marca:** el sistema no tiene marca. "Sistema Odontológico
  Multi-Sillón" es una etiqueta descriptiva del dominio, no un nombre comercial.
- **Logo:** no existe. `assets/logo.svg` es un marcador provisorio que dice
  "LOGO PROVISORIO".
- **Imágenes:** no hay registro fotográfico ni ilustración aprobada. No se usan
  fotos de stock, de pacientes ni imágenes clínicas.
- **Tipografía:** se usa el stack del sistema (`ui-sans-serif`, `system-ui`) para
  evitar fuentes remotas. Si el proyecto adopta una familia propia, debe
  alojarse localmente y actualizar `--font-sans`.
- **Iconografía:** no hay set aprobado; la fundación usa texto y SVG inline.
- **Tema oscuro:** no aprobado. `tokens.css` deja el punto de extensión
  comentado; no se implementa hasta que se pida.
- **Densidad vs. accesibilidad:** la agenda interna es densa. La fundación
  mantiene tipografía de 11–14px pero exige 44px de alto en controles
  interactivos. Si el usuario prefiere una densidad aún mayor en escritorio, es
  una decisión pendiente.

## Fuera de alcance de esta revisión

- Mockups por cambio (`design-mockups` los crea y los aprueba aparte).
- Componentes React reutilizables o migración del frontend a estos tokens.
- Tema oscuro, iconografía propia, fotografía, motion avanzado.
- Cualquier servicio externo, fuente remota o cuenta de terceros.
