# Design — C-09a agenda-dominio-avanzado

## Context

Ver `proposal.md` — Why. `Turno` tiene 5 estados (`reservado`, `confirmado`, `presente`, `atendido`, `cancelado`), `fin = inicio + duracion_min`, índices por sillón/profesional y antisolapamiento en servicio (DD-03). No hay reprogramación, sobreturnos ni `ausente`. La última migración es `0003`.

## Goals / Non-Goals

**Goals:**

- Mover un turno sin romper el antisolapamiento.
- Permitir sobreturnos explícitos y auditables.
- Respetar una ventana de cancelación en el portal público.
- Incorporar `ausente` para no-show.

**Non-Goals:**

- Vista semanal (C-09b).
- Reprogramación pública con token (C-10).
- Reportes de ausentismo (C-21).
- Reprogramación masiva o recurrente.

## Decisions

### D1 — Reprogramación con exclusión del propio turno

`PATCH /turnos/{id}/reprogramar` acepta `inicio` y `duracion_min` opcional. Mantiene `paciente_id`, `profesional_id` y `sillon_id`; recalcula `fin`; busca solapamientos excluyendo el turno actual; solo permite estados `reservado` o `confirmado`.

- **Por qué**: mover un turno no debe chocar consigo mismo; un turno atendido/cancelado/ausente no se reprograma.
- **Alternativa descartada**: cancelar + crear (pierde trazabilidad y puede fallar a mitad).

### D2 — Sobreturno como endpoint separado

`POST /turnos/sobreturno` recibe los datos del turno + `motivo_sobreturno`. Toma `autorizado_por` del JWT (`admin` o `recepcion`), setea `es_sobreturno=True` y **omite** la validación de solapamiento.

- **Por qué**: el sobreturno es una decisión explícita y auditable; no se mezcla con la creación normal ni con el portal público.
- **Alternativa descartada**: flag en `TurnoCreate` (el portal podría intentar usarlo).
- **Riesgo aceptado**: puede generar dos turnos en el mismo horario; es el propósito del sobreturno.

### D3 — Ventana de cancelación solo para el portal público

`Settings.cancelacion_min_horas` (default 12). `PublicReservaService.cancelar_por_token` rechaza con 409 si `inicio - ahora() < ventana`. La recepción puede cancelar desde `PATCH estado` sin restricción (override operativo).

- **Por qué**: el paciente no debe cancelar a último momento; recepción sí puede resolver excepciones.
- **Alternativa descartada**: aplicar la ventana también a recepción (bloquearía casos reales).
- **Zona**: se usa `ahora()` de `core/timezone` (ART).

### D4 — Estado `ausente`

Se agrega `ausente` al `CHECK` de `Turno.estado` y al `Literal` de `TurnoEstadoUpdate`. La UI lo muestra con color propio y permite marcarlo desde el menú de estado. No borra el turno.

- **Por qué**: no-show es un hecho operativo distinto de `cancelado`.
- **Alternativa descartada**: reutilizar `cancelado` (rompe reportes de ausentismo).

### D5 — Migración `0004`

- `es_sobreturno BOOLEAN NOT NULL DEFAULT false`
- `motivo_sobreturno VARCHAR(255) NULL`
- `autorizado_por UUID NULL` FK `usuarios.id`
- `CHECK` de estado ampliado a `ausente`
- `CHECK` de coherencia: si `es_sobreturno` entonces `motivo_sobreturno` no vacío.
- Downgrade reversible.

### D6 — UI

- Menú de estado agrega `ausente`.
- Acción “Reprogramar” abre un modal con fecha/hora y duración; usa el nuevo endpoint.
- Acción “Sobreturno” disponible para admin/recepción, pide motivo.
- Sin tests de componentes; `tsc`, `eslint` y `build`.

## Risks / Trade-offs

- [Sobreturnos sin límite] → es deliberado; se audita en C-20 y se reporta en C-21.
- [Reprogramación concurrente] → el servicio revalida; la carrera extrema queda como deuda (no hay `EXCLUDE`).
- [Ventana de cancelación] → configurable por entorno; no hay UI de configuración (C-19/C-20).
- [Migración en datos existentes] → `ausente` no afecta filas actuales; defaults seguros.

## Migration Plan

1. `alembic upgrade head` aplica `0004`.
2. Verificar columnas/constraints en PostgreSQL.
3. `alembic downgrade 0003` elimina columnas y restaura el `CHECK`; los turnos `ausente` se convierten a `cancelado`.
4. La suite completa dos veces.

## Open Questions

- ¿La ventana de cancelación debe ser por prestación? Queda a nivel consultorio por ahora.
- ¿El sobreturno requiere aprobación del admin o alcanza recepción? Se permite admin/recepción.
