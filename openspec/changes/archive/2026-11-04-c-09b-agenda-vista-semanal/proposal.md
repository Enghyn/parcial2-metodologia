# Proposal — C-09b agenda-vista-semanal

## Why

La agenda interna solo permite ver un día por vez, obligando a recepción a navegar siete veces para planificar la semana y detectar huecos entre sillones. La grilla semanal 7 días × 3 sillones (US-001) necesita además una fuente de datos eficiente: siete llamadas diarias en paralelo generan latencia, estados de carga inconsistentes y riesgo de solapamientos visuales entre días.

## What Changes

- Extender `GET /api/v1/turnos` con un rango de fechas de calendario `desde` / `hasta` (ambos inclusive, interpretados en ART) para devolver la semana completa en **una sola request**. Los filtros existentes `fecha`, `profesional_id` y `sillon_id` siguen funcionando sin cambios de contrato.
- Agregar un índice B-tree sobre `turnos.inicio` (migración `0005`) para sostener el filtro por rango con el volumen esperado.
- Agregar la ruta interna `/app/agenda/semana` con una grilla de 7 columnas (lunes a domingo) × 3 filas (un sillón por fila), navegación de semana anterior/siguiente/actual y filtro por profesional.
- Agregar un conmutador Diaria / Semanal. La vista diaria `/app/agenda` conserva su comportamiento actual.
- Reutilizar `EstadoTurnoMenu` y `ReprogramarModal` de C-09a para operar un turno desde la grilla semanal. **No** se agrega creación de turnos clickeando una celda vacía.
- Diferenciar visualmente los seis estados (incluido `ausente`) y marcar los sobreturnos con un indicador textual además del color.

**BREAKING:** ninguna. El rango es aditivo y opcional; `fecha` mantiene su semántica.

## Capabilities

### New Capabilities

Ninguna. La vista semanal pertenece a `internal-agenda` y el rango de listado a `agenda`.

### Modified Capabilities

- `agenda`: el requisito de listado incorpora `desde`/`hasta`, validación del rango y orden determinista; el requisito de zona horaria incorpora los límites del rango en ART.
- `internal-agenda`: se agregan los requisitos de vista semanal, navegación, filtro por profesional, conmutador, acciones reutilizadas, estados visuales/sobreturno y carga en una sola consulta.

## Impact

- **Backend**: `modules/agenda/schemas.py` (filtro de consulta), `service.py` (`listar` por rango), `router.py` (`GET /turnos`), `models.py` (índice), migración `0005`, tests de servicio/router/migración/zona horaria.
- **Frontend**: `app/router.tsx`, `features/agenda/` (página semanal, grilla, helpers puros, conmutador, filtro), `shared/api/agenda.ts` (parámetros de rango), `shared/date.ts` (inicio de semana ART), tests puros en `frontend/test/`.
- **Datos**: sin cambios de columnas ni de tipos; solo un índice nuevo y reversible.
- **Dependencias**: C-05 (agenda diaria) y C-09a (reprogramación, `ausente`, sobreturnos) ya archivados.
- **Fuera de alcance**: creación por click en celda vacía, drag & drop, vista mensual, recurrencia, visualización de bloqueos/feriados en la grilla, reportes de ocupación y reprogramación pública (C-10/C-21).
