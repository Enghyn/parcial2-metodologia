# Proposal — C-04b agenda timezone hardening

## Why

C-04, C-05 y C-06 dejaron una inconsistencia funcional: el portal público genera y muestra horarios en UTC, mientras la agenda interna muestra la misma hora en hora local. Un turno reservado para las 09:00 en el portal se guarda como `09:00Z` y aparece como **06:00** en la agenda interna. Además, el backend acepta turnos sobre sillones/profesionales/pacientes dados de baja y fechas pasadas.

## What Changes

- **Zona canónica `America/Argentina/Buenos_Aires` (ART)**: un helper único en backend para límites de día, combinación fecha+hora y normalización de datetimes naive.
- **Agenda interna**: el filtro `fecha` y la creación de turnos usan el día calendario ART; un `inicio` naive se interpreta como ART, no UTC.
- **Reserva pública**: la disponibilidad se genera en ART y se expone como instantes UTC correctos; el portal y la agenda interna muestran la misma hora ART.
- **Recursos vigentes**: crear un turno exige sillón, profesional y paciente activos y sin `deleted_at`; si no, responde 404.
- **Fechas futuras**: se rechaza un turno con `inicio` anterior al momento de la creación.
- **Frontend**: `formatHora` y el formateo público se unifican en ART; el modal interno convierte el input local a UTC explícitamente.
- **Tests**: helpers de timezone, borde de día ART, slots 09:00 ART = 12:00Z, recursos dados de baja y fechas pasadas.

## Capabilities

### New Capabilities

- Ninguna.

### Modified Capabilities

- `agenda`: día calendario ART, recursos vigentes y rechazo de fechas pasadas.
- `internal-agenda`: horarios mostrados en ART.
- `public-reservation`: disponibilidad y confirmación en ART, sin slots pasados.

## Impact

- **Backend**: nuevo `backend/src/app/core/timezone.py`; cambios en `modules/agenda/{service,schemas}.py` y `modules/public/{service,schemas}.py`.
- **Frontend**: `features/agenda/{dateUtils.ts,TurnoModal.tsx}` y `features/reserva-publica/{types.ts,steps/PasoHorario.tsx,TurnoPublicoPage.tsx}`.
- **Tests**: nuevos tests de timezone y actualización de los de agenda/público.
- **Sin migraciones ni dependencias nuevas.**
- **Fuera de alcance**: privacidad del paciente público (C-06b), limpieza de lint/suite (chore-quality-gate), carrera de concurrencia del antisolapamiento (DD-03) y transiciones de estado (solo catálogo).
