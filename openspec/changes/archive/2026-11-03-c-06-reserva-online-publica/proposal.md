# Proposal — C-06: reserva-online-publica

## Why

C-04 dejó la capa de servicios `TurnoService` (anti-solapamiento RN-AG-01, bloqueos RN-AG-04, cálculo de `fin` RN-AG-02) y C-05 la agenda interna, pero el paciente aún no puede auto-agendar: no existe portal público sin login, ni consulta de turno por token, ni enlace Click-to-Chat de WhatsApp (RN-G-01). C-06 cierra el Flujo 1 (reserva pública) reutilizando `TurnoService` para el cálculo de huecos, sin duplicar reglas (R6) ni alterar el esquema (R5).

## What Changes

- Nuevo módulo backend `modules/public/` (o extensión de `agenda`) con 4 endpoints sin autenticación bajo `/api/v1/public/*`:
  - `GET /api/v1/public/disponibilidad` — huecos libres cruzando sillones y profesionales para una prestación + profesional + fecha.
  - `POST /api/v1/public/reservar` — crea el turno en estado `reservado`, emite `token_publico`, find-or-create de `Paciente` por DNI.
  - `GET /api/v1/public/turnos/{token}` — vista pública del turno (sin IDs internos).
  - `POST /api/v1/public/turnos/{token}/cancelar` — cancelación autónoma (estado `cancelado`).
- Schemas Pydantic con `extra="forbid"` (R1), validación estricta de entrada (RN-SEG-01/R8).
- Reuso de `TurnoService`/`solapamiento`/`detectar_conflicto` para el cálculo de slots; no se duplica la lógica de antisolapamiento.
- Frontend: `/reservar` wizard de 4 pasos (prestación → profesional → día/hora → datos del paciente) y `/p/turno/:token` (confirmación + botón "Enviar aviso por WhatsApp" abriendo `https://wa.me/<telefono>?text=...` en nueva pestaña, RN-G-01).
- Configuración de horas laborales por defecto (08:00–20:00, grilla 30 min) documentada como supuesto (KB 09/10) y teléfono del consultorio vía env `WHATSAPP_CONSULTORIO`.
- Sin migración Alembic nueva: `token_publico` ya existe; la cancelación solo cambia `estado` (R13: sin borrado físico).

## Capabilities

### New Capabilities

- `public-reservation`: Portal público de reserva online y consulta/cancelación de turno por token opaco, incluyendo cálculo de huecos libres cruzando sillones y profesionales, find-or-create de paciente por DNI, y enlace Click-to-Chat de WhatsApp (RN-G-01, RN-AG-06, RN-SEG-01).

### Modified Capabilities

- (ninguna — `agenda` y `core-data-model` no cambian a nivel de requisitos; C-06 consume `TurnoService` y el esquema existente).

## Impact

- **Código backend**: nuevo `modules/public/` (o `modules/agenda/public_router.py`) + montaje en `app/api/v1/router.py`; reuso de `modules/agenda/service.py` y `modules/clinica/models.py` (Paciente).
- **Código frontend**: `features/reserva-publica/*`, actualización de `app/pages.tsx` (ReservarPage/TurnoPublicoPage) y `app/router.tsx` (rutas ya declaradas).
- **Config**: nueva env `WHATSAPP_CONSULTORIO` (teléfono receptor), `PUBLIC_SLOT_START`/`PUBLIC_SLOT_END` opcionales con defaults 08:00/20:00 y grilla 30 min.
- **Dependencias**: sin nuevas (reusa FastAPI/SQLAlchemy/Pydantic/React/Zustand/Tailwind).
- **Tests**: pytest TDD para slot computation y find-or-create paciente; verificación frontend por `tsc --noEmit` + `eslint` + `vite build`.
- **Consumidores futuros**: C-07/C-08 reusan el patrón público y el find-or-create de paciente.