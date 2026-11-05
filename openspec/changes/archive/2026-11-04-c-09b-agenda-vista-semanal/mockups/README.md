# Mockups — C-09b `agenda-vista-semanal`

Mockups de la vista semanal 7 días × 3 sillones, creados **antes de aplicar** el change,
según la política `system-and-mockups` del proyecto.

- **Change:** `openspec/changes/c-09b-agenda-vista-semanal`
- **Capacidad afectada:** `internal-agenda` (7 requisitos agregados)
- **Sistema de diseño:** `design-system/` — **revisión 1**, `Approval: approved (2026-11-04, by user)`
- **Aprobación de estos mockups:** `approved (2026-11-04, by user)`
- **Fecha de creación:** 2026-11-04
- **Navegador de captura:** Chromium (Playwright MCP), `scale: css`

> La marca, el logo y los datos de ejemplo son **provisorios**. El nombre sale de
> `design-system/brand.js` (`[data-brand-name]`) y el logo de
> `design-system/assets/logo.svg`, que dice “LOGO PROVISORIO”. Nada de esto debe
> presentarse como identidad final.

---

## Pantallas

| Archivo | Qué muestra |
|---|---|
| `semana.html` | Vista semanal principal: app shell, cabecera de semana, navegación anterior/hoy/siguiente, conmutador Diaria/Semanal (Semanal activo), filtro por profesional, leyenda de estados y grilla 7 × 3 con chips densos. |
| `estados.html` | Catálogo de la celda: los 6 estados + 2 variantes de sobreturno, celda libre, columna de hoy, superposición normal + sobreturno, semana sin turnos, esqueleto de carga y banner de error con reintento. |
| `reprogramar.html` | Modal de reprogramación de C-09a abierto sobre la grilla semanal, más las tres salidas del caso (dentro de la semana, fuera de la semana, 409). |
| `previews/` | Capturas 390×844 y 1440×900 de las tres pantallas. |

### `semana.html`

- **7 columnas** `lun 2 nov → dom 8 nov 2026`, **3 filas** `Sillón 1..3`, con `Hoy`
  marcado en el encabezado (`mié 4 nov`) y en la columna.
- **32 turnos** repartidos: cubre los **seis estados** (`reservado`, `confirmado`,
  `presente`, `atendido`, `cancelado`, `ausente`) y **dos sobreturnos** con badge
  textual “SOBRETURNO” + borde discontinuo (mar 3 y jue 5, Sillón 2).
- **Superposición real**: el jueves 5 en el Sillón 2 conviven `10:00–10:30` (normal)
  y `10:15–10:45` (sobreturno) en la misma celda, ordenados por hora de inicio.
- **Celdas libres** en el domingo (los tres sillones) y el sábado en el Sillón 3,
  rotuladas “Libre” con texto alternativo para lectores de pantalla.
- **Cancelados** visibles, atenuados y tachados (no se ocultan): D10.
- **Mobile**: la grilla scrollea horizontalmente dentro de `.week-scroll`; la
  columna de sillón queda fija (`position: sticky; left: 0`), hay una pista visible
  (“Deslizá la grilla para ver los 7 días →”), una franja de degradado en el borde
  derecho y la siguiente columna aparece cortada como afordancia.

### `estados.html`

Cada variante incluye la etiqueta textual del estado dentro del chip; el color nunca
es el único portador de significado. Además:

- **Semana sin turnos**: `No hay turnos en esta semana` + CTA a la vista diaria.
- **Carga**: esqueleto con la forma 7 × 3 dentro de un contenedor con scroll propio,
  `role="status"`, `aria-busy="true"` y el texto “Cargando la semana…”.
- **Error**: banner `role="alert"` con qué pasó, qué hacer y botón `Reintentar`.

### `reprogramar.html`

- Overlay `--color-overlay` (negro/40) sobre la grilla semanal; modal `max-width: 28rem`,
  `Reprogramar turno`, descripción con el turno actual, `Nuevo inicio`,
  `Duración (min)`, `Cancelar` / `Reprogramar`: mismo shell que
  `frontend/src/features/agenda/ReprogramarModal.tsx`.
- El chip de origen queda marcado con un contorno punteado.
- Tres notas de diseño: (1) el turno se mueve de celda dentro de la semana,
  (2) **si el nuevo inicio cae fuera de la semana mostrada el turno desaparece de la
  grilla y se anuncia la semana de destino** sin auto-navegar, (3) ante un 409 el
  mensaje aparece dentro del modal y el turno conserva su horario.
- La app de fondo está marcada `inert` + `aria-hidden` para que el foco quede en el
  diálogo.

---

## Fuentes

| Fuente | Uso |
|---|---|
| `design-system/tokens.css` (rev. 1) | Todos los colores, tipografía, espaciado, radios, sombras, foco y movimiento. No hay valores literales de color salvo los derivados con `color-mix()` sobre tokens. |
| `design-system/brand.js` | `[data-brand-name]` en la topbar y el `<title>`. |
| `design-system/assets/logo.svg` | Logo provisorio en la topbar (`alt` explicando que es provisorio). |
| `design-system/components.html` | Topbar, botones, campos, badges de estado, chips, grilla semanal, modal, vacío, esqueleto y alertas. |
| `design-system/brand.md` | Voz rioplatense, montos ARS, fechas es-AR, reglas de logo e imágenes. |
| `design.md` (C-09b) | D5 semana lunes–domingo en ART, **D6** layout de grilla, **D7** filtro en cliente, **D8** ruta y conmutador, **D9** acciones de C-09a y reprogramación fuera de semana, **D10** estados y sobreturno, **D11** carga/error. |
| `specs/internal-agenda/spec.md` | Los 7 requisitos agregados (vista 7 × 3, navegación, filtro, conmutador, acciones, estados/sobreturno, carga en una sola consulta). |
| `frontend/src/features/agenda/*` | Densidad, jerarquía y microcopy reales de `TurnoCard`, `AgendaColumn`, `EstadoTurnoMenu`, `ReprogramarModal`, `AgendaPage`. |
| `frontend/src/index.css` | Tokens base que la fundación ya hereda. |

### Requisito de la spec ↔ pantalla

| Requisito | Dónde se ve |
|---|---|
| Vista semanal 7 × 3 | `semana.html` (7 columnas, 3 filas, celdas con estado vacío) |
| Navegación de semana | `semana.html` (Semana anterior / Hoy / Semana siguiente + rango de la semana) |
| Filtro por profesional | `semana.html` (`Todos los profesionales` + 2 profesionales) |
| Conmutador Diaria/Semanal | `semana.html` (Semanal activo con `aria-current="page"` y “(vista activa)” para lectores) |
| Acciones de turno desde la grilla | `semana.html` (chips accionables) + `reprogramar.html` (modal y sus tres salidas) |
| Estados visuales y sobreturnos | `semana.html` + `estados.html` (6 estados, 2 sobreturnos, cancelado visible) |
| Carga semanal en una sola consulta | `estados.html` (esqueleto de una carga 7 × 3 y error con reintento) |

---

## Cómo previsualizar

1. **Abrir el archivo directamente** (no requiere build ni red):

   ```text
   openspec/changes/c-09b-agenda-vista-semanal/mockups/semana.html
   openspec/changes/c-09b-agenda-vista-semanal/mockups/estados.html
   openspec/changes/c-09b-agenda-vista-semanal/mockups/reprogramar.html
   ```

2. **Si el navegador bloquea los assets locales** (o si `file:` está bloqueado, como
   en el Playwright MCP de este entorno), servir la raíz del repo:

   ```powershell
   python -m http.server 8766 --directory .
   ```

   y abrir
   `http://localhost:8766/openspec/changes/c-09b-agenda-vista-semanal/mockups/semana.html`
   (idem `estados.html` y `reprogramar.html`). Detener con `Ctrl+C`.

3. Revisar en **390×844** y **1440×900**. Las rutas relativas a
   `../../../../design-system/` solo funcionan si la carpeta `openspec/` sigue
   dentro del repo; no mover los HTML a otra ubicación.

No hay fuentes remotas, CDN, dependencias ni imágenes externas: solo los tokens y el
logo local.

---

## Capturas renderizadas

Generadas con Playwright MCP el 2026-11-04, página completa, `scale: css`
(el ancho útil es 375/1425 px por la barra de scroll del viewport).

| Captura | Pantalla | Viewport |
|---|---|---|
| `previews/semana-390x844.png` | `semana.html` | 390×844 |
| `previews/semana-1440x900.png` | `semana.html` | 1440×900 |
| `previews/estados-390x844.png` | `estados.html` | 390×844 |
| `previews/estados-1440x900.png` | `estados.html` | 1440×900 |
| `previews/reprogramar-390x844.png` | `reprogramar.html` | 390×844 |
| `previews/reprogramar-1440x900.png` | `reprogramar.html` | 1440×900 |

Verificado en las capturas y por medición en el DOM:

- Sin scroll horizontal de página en ninguno de los dos anchos
  (`documentElement.scrollWidth === innerWidth`).
- Sin errores de consola ni requests fallidos (4 requests locales, todas 200:
  HTML, `tokens.css`, `logo.svg`, `brand.js`).
- Anillo de foco visible con teclado (azul primario, 2px, offset 2px).

---

## Excepción de densidad (documentada)

> **Excepción de densidad:** la grilla semanal usa **micro-tipografía de 10px**
> (`0.625rem`) para la línea de metadatos del chip (prestación · profesional), la
> etiqueta de estado y el badge “Sobreturno”, igual que `TurnoCard.tsx`,
> `EstadoTurnoMenu.tsx` (`text-[10px]` / `text-[11px]`) y `.turno__state` en
> `design-system/components.html`. Es una excepción **solo tipográfica** al rango
> 11–14px de la fundación: **ningún objetivo táctil baja de 44px**. Los chips miden
> 67–85px de alto, los botones, enlaces y selects 44px o más, y no se usó la
> excepción de “chips de 20–28px” prevista en el brief.

---

## Accesibilidad

- HTML semántico: `<table>` con `<caption>`, `scope="col"`/`scope="row"`, navegación
  con `aria-label`, `<main>`, `skip-link`.
- **Nunca solo color**: cada chip lleva el estado en texto (mayúscula, 10px), y el
  sobreturno agrega la palabra “SOBRETURNO” y borde discontinuo.
- Cancelados atenuados **y** tachados, pero presentes en el DOM y en la lectura.
- Foco visible en todos los interactivos (`:focus-visible` con `--focus-ring-color`).
- La grilla es `role="region"` con `tabindex="0"` para poder scrollearla con teclado.
- La topbar móvil oculta el chip de sesión (decorativo) para no romper la fila; la
  navegación conserva 44px de alto.
- `prefers-reduced-motion`: se anula el shimmer del esqueleto y el hover de los chips.
- `reprogramar.html`: fondo `inert` + `aria-hidden`, diálogo con `aria-modal="true"`
  y `aria-labelledby`/`aria-describedby`.

---

## Decisiones de layout y límites conocidos

1. **Chip sin posicionamiento proporcional al tiempo** (D6): la celda lista chips
   ordenados por hora. La vista diaria conserva el detalle temporal.
2. **Encabezado y columna sticky**: en escritorio (≥901px) el `thead` es
   `position: sticky; top: 0` contra el scroll de la página y se verificó que queda
   fijo al desplazarse. En mobile/tablet la grilla tiene su propio scroller
   horizontal, así que se prioriza la **columna de sillón fija** y el encabezado deja
   de ser sticky (un elemento con `overflow` propio no puede fijar el `thead` contra
   el viewport). Es una limitación de CSS asumida, no un olvido.
3. **Sin bloqueos ni feriados** en la grilla: fuera de alcance de C-09b (gap conocido
   en `design.md`). Por eso no se inventaron bloqueos en el mockup.
4. **Domingo sin turnos** en el ejemplo: sirve para mostrar el día vacío y los huecos.
   No se incluyó el caso “turno 23:30 del domingo” del escenario de zona horaria
   porque no es un horario de consultorio realista; el escenario se cubre con tests,
   no con el mockup.
5. **Datos ficticios**: pacientes y profesionales son inventados para el mockup; no
   corresponden a personas reales ni a datos clínicos.

---

## Marcadores `(TBD)` abiertos

| Marcador | Dónde | Reemplazo |
|---|---|---|
| Nombre de marca | Topbar y `<title>` vía `[data-brand-name]` | Editar `BRAND_NAME` en `design-system/brand.js` (no tocar los HTML). |
| Logo “LOGO PROVISORIO” | `design-system/assets/logo.svg` en la topbar | Reemplazar el archivo por el logo aprobado, misma ruta. |
| Identidad de la sesión | Chip “Recepción” | Usuario real cuando exista sesión; hoy solo indica el rol. |
| Iconografía | Flechas `←`/`→` y `×` tipográficos | Set de íconos aprobado (la fundación no tiene uno). |
| Profesionales / pacientes de ejemplo | Chips de la grilla y modal | Datos reales del consultorio. |
| Montos en ARS | No aplica en esta pantalla | El modal no muestra importes; si se agrega seña, usar `$ 12.500`. |

---

## Qué revisar antes de aprobar

- Que la densidad de la grilla sea usable en el escritorio de recepción (7 columnas
  con chips de 4 líneas).
- Que “Libre” y los estados se distingan sin depender del color.
- Que el tratamiento del **sobreturno** (badge + borde discontinuo) y del
  **cancelado** (atenuado + tachado) sea el esperado.
- Que el aviso de **reprogramación fuera de la semana** (y el 409) tenga el tono
  correcto.
- Que el conmutador Diaria/Semanal y el filtro por profesional estén en el lugar
  donde los espera recepción.

Con aprobación explícita, actualizar `## UI Mockups` en `design.md` a
`Approval: approved (AAAA-MM-DD, by user)` y recién entonces pasar a aplicar el
change. Cualquier cambio visual posterior obliga a re-renderizar los previews.
