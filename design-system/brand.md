# Marca y tono visual

> Estado: **provisoria**. Nada de este documento debe presentarse como identidad
> final. Todo lo marcado `(TBD)` requiere decisión del usuario.

## Nombre del producto

- **Nombre mostrado:** `Consultorio (marca provisoria)` — `(TBD)`.
  - Fuente del valor: `brand.js` (`BRAND_NAME`). Es el único lugar donde se cambia.
- **Etiqueta descriptiva del dominio:** "Sistema Odontológico Multi-Sillón".
  - Fuente: `knowledge-base/01_vision_y_objetivos.md` y `AGENTS.md`.
  - Se usa para describir el producto, **no** como marca comercial. No inventar
    tagline, razón social, ni nombre de cliente.
- **Idioma:** español rioplatense (voseo), montos en ARS.
  - Fuente: regla dura R10 en `AGENTS.md`.

## Audiencia y contexto de uso

| Audiencia | Contexto | Implicancia visual |
|---|---|---|
| Recepción / secretaría | Escritorio, jornada completa, alta frecuencia de uso | Densidad alta, acciones rápidas, texto legible, poco cromo |
| Odontólogos | Escritorio o tablet durante la atención | Jerarquía clara, estados distinguibles, sin decoración que compita con el dato clínico |
| Administración / dueño | Escritorio, supervisión y caja | Tablas y métricas sobrias, montos alineados y tabulares |
| Paciente (público) | Celular, sin login, primera visita | Formularios de 16px, pasos simples, botones grandes, copy claro |

Fuentes: `knowledge-base/01_vision_y_objetivos.md`, `knowledge-base/03_actores_y_roles.md`,
`knowledge-base/06_funcionalidades.md` (US-001 y criterios de agenda), `AGENTS.md`.

## Tono visual

**Clínica, calma y de baja decoración.** Es una herramienta de trabajo, no una
página de marketing.

- **Claridad primero:** el dato operativo (hora, paciente, sillón, estado, monto)
  manda sobre el adorno.
- **Baja cromía:** blanco, grises neutros y un único azul de acción
  (`--color-primary`). El color se reserva para estados y alertas.
- **Densidad controlada:** la agenda interna usa tipografía de 11–14px y
  espaciado de 4px, sin sacrificar objetivos táctiles de 44px.
- **Bordes finos y sombras discretas:** cards de 1px, radio 4px, sombra solo en
  modales y elevaciones reales.
- **Movimiento sobrio:** 100–240ms, `ease-out`, solo color/opacidad/transform.
  Se reduce a casi cero con `prefers-reduced-motion`.
- **Copy:** instrucciones directas y breves; estados en minúscula dentro de la
  card y en mayúscula solo para etiquetas de columna o acciones micro.

Fuente: auditoría de `frontend/src/index.css`,
`frontend/src/features/agenda/*`, `frontend/src/features/caja/CajaPage.tsx` y
`frontend/src/app/layout.tsx`. El tono clínico se deriva del dominio descrito en
`knowledge-base/01_vision_y_objetivos.md`.

## Reglas de logo

- **Marcador provisorio:** `assets/logo.svg` dice visiblemente "LOGO PROVISORIO".
  No es una identidad final ni debe usarse en material comercial.
- **Ruta estable:** los mockups referencian siempre `design-system/assets/logo.svg`.
  Reemplazar ese archivo por el logo aprobado, sin tocar los HTML.
- **Área de resguardo:** mínimo media altura del logo libre alrededor.
- **Tamaño mínimo:** 120px de ancho en pantalla; por debajo, usar solo el nombre.
- **Fondo:** funciona sobre `--color-surface` (blanco). Si el logo final no tiene
  contraste suficiente, entregar una variante para fondos oscuros.
- **No hacer:** recolorear el logo provisorio, estirarlo, rotarlo ni presentarlo
  como marca definitiva.

## Reglas de imágenes

- **Sin fotos de stock** ni imágenes de pacientes, dientes reales o radiografías.
  `(TBD)` si el producto necesitará fotografía clínica en el futuro.
- **Sin imágenes remotas** en la fundación ni en los mockups: todo asset es local.
- **Ilustración permitida:** line-art esquemático (por ejemplo, odontograma FDI)
  en `--color-border-strong` sobre fondo blanco, sin texto incrustado.
- **Iconografía:** `(TBD)`. Mientras no exista un set aprobado, usar texto,
  símbolos tipográficos o SVG inline simples; nunca depender solo del icono para
  comunicar un estado.

## Voz y microcopy

- Voseo rioplatense: "Elegí", "Completá", "Revisá", "Volvé a intentar".
- Montos: `$ 12.500` (separador de miles con punto, sin decimales salvo que el
  cobro los requiera).
- Fechas y horas: `es-AR`, formato 24h (`09:30`).
- Errores: qué pasó + qué hacer ("El sillón 2 ya tiene un turno en ese horario.
  Elegí otro horario o profesional.").
- Nunca mostrar datos sensibles de salud en URLs, logs ni mensajes de error
  (R9 en `AGENTS.md`).

## Decisiones abiertas

Ver la lista completa y literal en `README.md` → **Decisiones abiertas (TBD)**.
