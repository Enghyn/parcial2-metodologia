# Proposal — C-09a agenda-dominio-avanzado

## Why

El MVP base de agenda permite crear turnos, listar, cambiar estado y bloquear, pero no cubre tres operaciones reales del consultorio: **reprogramar** un turno, **sobreturnar** con autorización y **cancelar fuera de una ventana mínima**. Tampoco existe el estado `ausente` (no-show), que alimenta el ausentismo de C-21.

## What Changes

- **Reprogramación**: `PATCH /api/v1/turnos/{id}/reprogramar` con nuevo `inicio` y `duracion_min` opcional; valida solapamiento excluyendo el propio turno.
- **Sobreturnos**: `POST /api/v1/turnos/sobreturno` con motivo obligatorio y autorizador tomado del JWT; permite solapamiento deliberado.
- **Ventana de cancelación**: `cancelacion_min_horas` configurable (default 12 h); la cancelación pública fuera de ventana responde 409. La recepción puede cancelar con override.
- **Estado `ausente`**: se agrega al catálogo de estados y a la UI; no es un borrado.
- **Migración `0004`**: columnas de sobreturno/autorizador y `CHECK` de estado ampliado.

## Capabilities

### New Capabilities

- Ninguna.

### Modified Capabilities

- `agenda`: reprogramación, sobreturnos, ventana de cancelación y estado `ausente`.
- `internal-agenda`: acciones de reprogramar y marcar ausente en la agenda interna.
- `public-reservation`: cancelación pública sujeta a la ventana mínima.

## Impact

- **Backend**: `modules/agenda/{models,schemas,service,router}.py`, `core/config.py`, migración `0004`.
- **Frontend**: `features/agenda/*` (acción reprogramar/ausente) y `estadoColor`.
- **Tests**: esquemas, servicio y router de agenda; migración; ventana de cancelación.
- **Sin integraciones externas.**
- **Fuera de alcance**: vista semanal (C-09b), reprogramación pública (C-10) y reportes de ausentismo (C-21).
