# Design — C-04b agenda timezone hardening

## Context

Ver `proposal.md` — Why. El backend usa `timestamptz` y los tests actuales trabajan en UTC; el frontend interno formatea en la zona del navegador y el público en UTC. La zona del consultorio es `America/Argentina/Buenos_Aires` (UTC-3, sin DST). No hay migración de schema: cambia la interpretación y la presentación de los instantes.

## Goals / Non-Goals

**Goals:**

- Un único criterio de zona para backend y ambas superficies.
- Que un turno de 09:00 ART se vea 09:00 en el portal y en la agenda interna.
- Que no se pueda reservar sobre recursos dados de baja ni en el pasado.

**Non-Goals:**

- Cambiar el modelo de datos o agregar `EXCLUDE` (sigue DD-03).
- Resolver la privacidad del paciente público (C-06b).
- Limpiar lint o hacer hermética la suite (chore-quality-gate).
- Validar secuencias de estados (el spec solo exige catálogo).

## Decisions

### D1 — Zona canónica en un helper

`app/core/timezone.py` expone `TZ_CONSULTORIO`, `ahora()`, `inicio_dia(fecha)`, `fin_dia(fecha)`, `combinar(fecha, hora)` y `normalizar_entrada(datetime)`.

- **Por qué**: evita repetir `ZoneInfo` y offsets en servicios y tests.
- **Alternativa descartada**: usar `datetime.now().astimezone()` (depende de la máquina) o hardcodear `-03:00` en el backend (opaco).

### D2 — Día calendario y slots en ART

- `TurnoService.listar(fecha)` usa `[inicio_dia(fecha), fin_dia(fecha))` en ART.
- `PublicReservaService.disponibilidad(fecha)` genera `combinar(fecha, hora)` en ART y descarta slots `<= ahora()`.
- `SlotOut.inicio` es un `datetime` aware; al serializarse conserva el instante correcto.

- **Por qué**: el negocio razona en el día del consultorio, no en UTC.
- **Alternativa descartada**: mantener UTC y formatear todo en UTC (el portal y la agenda mostrarían 06:00 o 09:00 según el cliente; no es aceptable).

### D3 — Naive = ART

`TurnoCreate` y `ReservaCreate` interpretan un `datetime` sin tzinfo como ART y lo devuelven aware. Un datetime con offset se respeta.

- **Por qué**: el `<input type="datetime-local">` del modal envía hora de pared del consultorio; asumir UTC desplaza 3 horas.
- **Alternativa descartada**: rechazar naive con 422 (rompe el cliente actual y la KB no lo exige).

### D4 — Recursos vigentes y fechas futuras

`TurnoService.crear` valida:
- `Sillon`, `Profesional` y `Paciente` existentes, `activo=True` y `deleted_at IS NULL`; si no, 404.
- `inicio > ahora()`; si no, 422.

- **Por qué**: las FKs solo garantizan existencia; un recurso con borrado lógico sigue existiendo. Una reserva en el pasado no tiene sentido operativo.
- **Alternativa descartada**: validar solo en schemas (no cubre IDs arbitrarios) o confiar en el frontend.

### D5 — Formateo único en el frontend

`features/agenda/dateUtils.ts` exporta `formatHora` con `timeZone: "America/Argentina/Buenos_Aires"` y `toIsoDate`/`localInputToUtc` en ART. `features/reserva-publica/types.ts` deja de usar `formatHoraUtc`/`formatFechaUtc` y reusa el mismo criterio.

- **Por qué**: el navegador puede estar en otra zona; la clínica no.
- **Alternativa descartada**: `toLocaleTimeString` sin `timeZone` (depende de la máquina del usuario).

### D6 — Tests por capas

1. Helpers puros de timezone: 09:00 ART = 12:00Z; borde 00:00 ART.
2. Servicios con DB: día ART, slots, recursos dados de baja, fecha pasada.
3. Frontend: `tsc`, `eslint` y build; sin runner de tests (limitación aceptada en C-05).

- **Por qué**: los tests actuales en UTC no detectan el desfase.
- **Alternativa descartada**: sumar un runner de frontend en este change (fuera de alcance).

## Risks / Trade-offs

- [Tests existentes asumen UTC] → se actualizan a ART explícita; los que usan `2027` siguen siendo futuros.
- [Argentina sin DST] → el offset es fijo; si cambia la regla, se actualiza `TZ_CONSULTORIO` y los tests.
- [Slots pasados el mismo día] → se filtran con `<= ahora()`; el portal no ofrece horarios vencidos.
- [Cambio de comportamiento de naive] → documentado en la spec; el modal envía ART explícito.

## Migration Plan

1. Tests de timezone en rojo.
2. Helper + servicios + schemas.
3. Frontend.
4. Suite backend con PostgreSQL, `tsc`, `eslint` y `build`.
5. Sin migración de base.

## Open Questions

- ¿La grilla pública debe excluir el día actual si ya no quedan slots? (Se resuelve devolviendo lista vacía; no cambia el contrato.)
- ¿Se agrega un catálogo `Prestacion`? Sigue en KB 10; no es parte de este change.
