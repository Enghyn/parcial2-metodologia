# Design — C-09b agenda-vista-semanal

## Context

Ver `proposal.md` — Why y los delta specs de `agenda` e `internal-agenda` para el contrato de comportamiento.

Estado actual relevante:

- `GET /api/v1/turnos` filtra por `fecha` (día ART), `profesional_id` y `sillon_id`; `TurnoService.listar` usa `inicio >= inicio_dia(fecha)` y `< fin_dia(fecha)` y ordena solo por `inicio`.
- Índices existentes: `ix_turnos_sillon_inicio_fin (sillon_id, inicio, fin)` e `ix_turnos_profesional_inicio_fin (profesional_id, inicio, fin)`. No hay índice que sirva un rango global por `inicio`.
- La SPA usa `/app/agenda` (`AgendaPage`) con una columna por sillón, `useAgendaStore` y los componentes de C-09a (`EstadoTurnoMenu`, `ReprogramarModal`). Los tests de frontend son `node:test` puros sobre módulos TS, sin DOM ni React Testing Library.
- Última migración: `0004_agenda_avanzada`.

## Goals / Non-Goals

**Goals:**

- Una sola request por semana y una sola fuente de verdad para turnos, sillones y profesionales.
- Contrato de `GET /turnos` aditivo y compatible con los consumidores actuales.
- Reutilizar las acciones de C-09a sin duplicar lógica de estado ni de reprogramación.
- Mantener la vista diaria intacta y el RBAC en backend (R8).
- Cubrir el rango con un índice adecuado y un plan de migración reversible.

**Non-Goals:**

- Crear turnos clickeando celdas vacías, drag & drop o redimensionado de turnos.
- Vista mensual, recurrencia, arrastre entre sillones.
- Resaltar el día de hoy en la grilla (no se implementa en este change).
- Mostrar bloqueos, feriados o mantenimiento en la grilla semanal (US-001 lo menciona; queda como gap conocido para un change futuro, porque la vista diaria tampoco los muestra hoy).
- Paginación del listado de turnos (el rango está acotado a 31 días).
- Cambios de modelo de datos más allá del índice.
- Tests de componentes React con DOM (no hay harness instalado; se cubre con tests puros + `tsc`/`eslint`/`build` + verificación manual/Playwright).

## Decisions

### D1 — Rango por fechas de calendario en el endpoint existente

`GET /api/v1/turnos` suma `desde` y `hasta` como `date` (no `datetime`), ambos inclusive. El servicio traduce a `Turno.inicio >= inicio_dia(desde)` y `Turno.inicio < fin_dia(hasta)`, reutilizando `core/timezone`. `fecha` sigue existiendo con su semántica actual.

- **Por qué**: el frontend razona en días ART; enviar `datetime` obligaría a construir offsets en el cliente y a duplicar la lógica de zona. Una request devuelve la semana completa.
- **Alternativa descartada**: endpoint `/turnos/semana` (duplica contrato y RBAC) y siete llamadas diarias (latencia, cargas parciales y riesgo de inconsistencia).
- **Compatibilidad**: `fecha` y el rango son mutuamente excluyentes; si conviven se responde 422 para evitar resultados ambiguos.

### D2 — Validación del rango en un schema de consulta

Se introduce `FiltroTurnos` (`BaseModel`, `model_config = ConfigDict(extra="forbid")`, R1) con `fecha`, `desde`, `hasta`, `profesional_id` y `sillon_id`, consumido como dependencia del handler. Reglas:

- `desde` y `hasta` van juntos: uno solo → 422.
- `desde <= hasta` → si no, 422.
- Rango máximo de 31 días de calendario (`(hasta - desde).days <= 30`) → si no, 422. Cubre una semana con margen y evita consultas sin cota.
- `fecha` junto a `desde`/`hasta` → 422.

Los 422 usan el handler existente de `RequestValidationError`, que ya devuelve `{error:{code,message,details}}`.

- **Por qué**: la validación vive en el borde HTTP y el servicio recibe un rango ya válido; los tests de schema pueden ejercitarla sin base.
- **Nota R1**: el schema declara `extra="forbid"`. Los query params desconocidos siguen ignorándose (comportamiento FastAPI actual) para no romper clientes; el `forbid` aplica al modelo, no al query string. Esto se documenta como trade-off, no como cambio de contrato.

### D3 — Orden determinista

`TurnoService.listar` ordena por `Turno.inicio ASC, Turno.sillon_id ASC, Turno.id ASC`. El orden por `inicio` se mantiene para la vista diaria; los desempates hacen estable la grilla y los tests.

- **Por qué**: dos turnos pueden compartir `inicio` (sobreturnos), y PostgreSQL no garantiza orden entre filas empatadas.
- **Alternativa descartada**: ordenar solo en el cliente (la API quedaría no determinista para otros consumidores).

### D4 — Índice de rango y migración `0005`

Se agrega `Index("ix_turnos_inicio", "inicio")` al modelo `Turno` y la migración `0005_agenda_indice_inicio` (`down_revision = "0004_agenda_avanzada"`), con `create_index`/`drop_index` reversibles.

- **Por qué**: el filtro global `deleted_at IS NULL AND inicio >= X AND inicio < Y ORDER BY inicio` no tiene un índice cuyo prefijo sea `inicio`; los existentes empiezan por `sillon_id` o `profesional_id`. Con 2–3 sillones y ~7 días el volumen es bajo, pero el índice evita un seq scan al crecer el histórico.
- **Alternativa descartada**: índice parcial `WHERE deleted_at IS NULL` (más eficiente, pero complica el modelo y el test de migración; se puede adoptar luego si el `EXPLAIN` lo justifica).
- **Nota**: no hay cambios de columnas ni de constraints; el downgrade solo elimina el índice.

### D5 — Semana lunes–domingo calculada en ART

La SPA calcula el lunes de la semana con `toIsoDate`/`addDays` y un helper puro nuevo (`inicioSemana`, `diasSemana`) sobre `TZ_CONSULTORIO`. Se envían `desde` = lunes y `hasta` = domingo en formato `YYYY-MM-DD`.

- **Por qué**: la semana operativa argentina arranca el lunes; construirla con `Date` local del navegador rompería en otras zonas.
- **Alternativa descartada**: domingo como primer día (no coincide con la operación del consultorio) y calcular la semana en el backend (el backend no necesita conocer la UI).

### D6 — Layout de la grilla semanal

Grilla CSS con:

- Fila de encabezado sticky con los siete días (nombre del día + fecha corta).
- Primera columna sticky con el nombre del sillón.
- Una fila por sillón activo y una celda por día.
- Cada celda lista “chips” compactos ordenados por hora; el chip muestra hora, paciente, estado y, si aplica, indicador de sobreturno.
- En desktop se ven las 7 columnas; en mobile la grilla scrollea horizontalmente con la columna de sillón fija.
- No hay posicionamiento proporcional al tiempo: la vista diaria ya cubre el detalle temporal. La semanal prioriza densidad y detección de huecos.

- **Por qué**: 7 × 3 = 21 celdas deben caber sin perder legibilidad; el layout por filas de sillón mantiene la lectura “quién ocupa qué espacio” de US-001.
- **Alternativa descartada**: grilla horaria 7 × horas (demasiado densa y con scroll bidimensional) y calendario de tarjetas por día (pierde la comparación entre sillones).

### D7 — Filtro por profesional en cliente

La semana se descarga una vez sin `profesional_id`; el filtro es un `<select>` con “Todos los profesionales” y se aplica con `useMemo` sobre el arreglo de turnos. El endpoint sigue aceptando `profesional_id` para consumidores directos.

- **Por qué**: cambiar de profesional no debe generar otra request ni un estado de carga; el volumen semanal es chico y el filtro es instantáneo.
- **Alternativa descartada**: filtrar en backend (más requests y parpadeo de la grilla). Si el volumen creciera, se migra sin cambiar la spec.

### D8 — Ruta y conmutador

- `/app/agenda` → vista diaria existente, sin cambios de comportamiento.
- `/app/agenda/semana` → nueva `SemanaPage`.
- Conmutador `Diaria | Semanal` en el encabezado de ambas vistas, con `NavLink`/`Link` y `aria-current` para la opción activa.
- Deep link directo a `/app/agenda/semana` soportado por `RequireAuth`.
- Al volver de semanal a diaria se navega a `/app/agenda` (la diaria sigue abriendo “hoy”, como hoy).

- **Por qué**: una ruta separada permite deep links, no mezcla estados de carga y deja la vista diaria testeada y estable.
- **Alternativa descartada**: query param `?vista=semana` en la misma página (complica el estado y el ciclo de carga).

### D9 — Reutilización de acciones de C-09a

La `SemanaPage` mantiene `turnoSeleccionado` y `reprogramando` como estado local y pasa callbacks a un `TurnoChip` que compone `EstadoTurnoMenu` (sin cambios) y un botón “Reprogramar” que abre el `ReprogramarModal` existente. El store se reutiliza (`cambiarEstado`, `reprogramar`), agregando solo la carga por rango.

- **Por qué**: una sola implementación de menú y modal evita divergencias de permisos y mensajes de error.
- **Alternativa descartada**: duplicar el menú dentro del chip (doble mantenimiento y riesgo de R8).
- **Click en celda vacía**: sin handler; no se abre `TurnoModal` ni se crea nada.
- **Reprogramación fuera de la semana**: si el nuevo `inicio` cae fuera del rango mostrado, el turno se quita de la grilla y se muestra un aviso con la semana de destino; no se auto-navega para no perder el contexto.

### D10 — Estados visuales y sobreturno

Se reutiliza `estadoClasses` para los seis estados. El chip agrega la etiqueta textual del estado (no solo color) y, si `es_sobreturno`, un badge “Sobreturno” y borde punteado. `cancelado` se muestra atenuado y tachado, pero visible. Se agrega una leyenda compacta sobre la grilla.

- **Por qué**: recepción necesita distinguir un no-show de una cancelación y un sobreturno de un turno normal; el color solo no es accesible.
- **Alternativa descartada**: ocultar cancelados (se pierde contexto operativo) y un color nuevo para sobreturno (rompe el mapa estado→color y el contraste de tokens).

### D11 — Performance y estado de carga

- Una request por semana; catálogos (`sillones`, `profesionales`, `pacientes`) se cargan en paralelo solo cuando faltan, como ya hace `useAgendaStore.cargar`.
- Agrupación `turno → (día, sillón)` en una sola pasada O(n) con `useMemo`.
- `loading` y `error` con reintento; al navegar de semana se reemplaza el arreglo completo (no se acumula).
- Sin `useEffect` que derive estado: la semana es estado explícito del store/página.

- **Por qué**: cumple “una sola consulta” y evita parpadeos; el filtro y la agrupación no recalculan en cada render.
- **Alternativa descartada**: siete llamadas con `Promise.all` (más latencia y estados parciales) y memoización por celda (el volumen no lo justifica).

### D12 — RBAC y privacidad

- El listado sigue protegido por `require_role("admin", "recepcion", "odontologo")`. La UI solo oculta acciones (R8).
- No se agregan datos de salud a logs ni a la URL: la ruta solo contiene la semana (`/app/agenda/semana` sin parámetros) y las requests llevan fechas, no datos de pacientes (R9).
- El frontend no usa `any`; componentes en `PascalCase` y retorno `ReactElement` (R7).

## Risks / Trade-offs

- [Rango máximo de 31 días] → puede bloquear un caso legítimo de “mes calendario” (31 días exactos sí entra; 32 no). Se documenta el límite en el mensaje 422 y se puede ampliar sin cambiar el contrato.
- [Índice simple en `inicio`] → menos selectivo que un parcial; aceptable para el volumen académico. Se reevalúa con `EXPLAIN ANALYZE` si el histórico crece.
- [Filtro en cliente] → la respuesta semanal trae todos los profesionales. Con 3 sillones y 7 días el payload es acotado; si crece, se mueve al backend sin cambio de spec.
- [Sin tests de DOM] → la lógica de semana, agrupación y filtro se cubre con tests puros; el render se valida con `tsc`, `eslint`, `build` y verificación manual/Playwright. Es una limitación del harness actual, no del cambio.
- [Grilla con scroll horizontal en mobile] → aceptable para una herramienta interna de escritorio; la columna de sillón queda fija para no perder contexto.
- [Cambio de query params desconocidos] → se mantiene el comportamiento actual (ignorados) para no romper clientes; el `extra="forbid"` del schema no altera el query string.
- [Bloqueos/feriados no visibles] → US-001 pide diferenciarlos y ni C-05 ni C-09b los muestran. Se registra como gap conocido; requiere un change propio porque implica exponer bloqueos en la grilla.

## Migration Plan

1. `cd backend && alembic upgrade head` aplica `0005_agenda_indice_inicio`.
2. Verificar `\d turnos` y que `ix_turnos_inicio` exista.
3. `alembic downgrade 0004_agenda_avanzada` elimina el índice sin tocar datos.
4. Correr `pytest -m "not integration" -q` y luego la suite completa con PostgreSQL migrado y sembrado.
5. Rollback de aplicación: el endpoint sigue aceptando `fecha`, por lo que un frontend viejo funciona contra el backend nuevo y viceversa (el rango es aditivo).
6. Frontend: `npm test`, `npm run lint`, `npx tsc --noEmit`, `npm run build`.

## UI Mockups

- **Design system revision:** 1 (`design-system/README.md`, `Approval: approved (2026-11-04, by user)`).
- **Decision:** yes (project policy `system-and-mockups`, recorded in `.active-orchestrator-state.json` as `visual_design.mode`).
- **Mockups:** `openspec/changes/c-09b-agenda-vista-semanal/mockups/` (`semana.html`, `estados.html`, `reprogramar.html`).
- **Approval:** approved (2026-11-04, by user).
- **Preview:** rendered (2026-11-04) — `mockups/previews/*.png` at 390×844 and 1440×900.
- **Visual verify:** differences (2026-11-04; reparado 2026-11-04) — contraste en Chromium a **320×844, 390×844 y 1440×900** contra `previews/semana-*.png`: grilla 7 × 3 con **columnas de igual ancho** (`table-fixed`; 155 px por día a 1440, 123 px en mobile), columna de sillón fija, columna de hoy, chips con estado textual, badge + borde discontinuo de sobreturno y cancelados atenuados; la cabecera diaria pasa a dos filas por debajo de `sm` (sin solapamientos ni recorte) y `/app/agenda` y `/app/agenda/semana` no generan scroll horizontal de página (`scrollWidth === clientWidth` a 320/390/1440). Siguen siendo diferencias respecto del mockup, no defectos: paleta Tailwind de `estadoColor.ts` en lugar de `design-system/tokens.css`, nombre completo del profesional en vez de iniciales, sin la línea “Unidad N” (la API no expone `descripcion`), “Cerrar sesión” extra en la cabecera y botones del menú de estado de 19–20 px (heredados de C-09a; deuda de a11y registrada como follow-up). El estado vacío por filtro de profesional sigue la spec (`internal-agenda`), no `estados.html`. Capturas: `mockups/verify/{diaria,semana}-{320x844,390x844,1440x900}.png`, `mockups/verify/semana-completa-{320x844,390x844,1440x900}.png`, `mockups/verify/semana-{vacia,error,reintento,filtro-sin-turnos}-1440x900.png`, `mockups/verify/reprogramar-{409,fuera-semana}-1440x900.png`.

## Open Questions

- ¿La semana debe recordar el último profesional filtrado entre recargas? Se deja sin persistencia (vuelve a “Todos”) hasta que exista una preferencia de usuario. No cambia el contrato ni las tareas.
