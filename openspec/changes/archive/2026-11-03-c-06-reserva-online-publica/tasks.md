# Tasks — C-06: reserva-online-publica

## 1. Backend — configuración y scaffolding del módulo public

- [x] 1.1 Agregar a `Settings` (`core/config.py`) los campos `public_slot_start`, `public_slot_end`, `public_slot_grid_min` con defaults `"08:00"`, `"20:00"`, `30`, y verificar que `test_settings.py` sigue pasando (`pytest backend/test/test_settings.py`).
- [x] 1.2 Crear el paquete `backend/src/app/modules/public/` con `__init__.py`, `schemas.py`, `service.py`, `router.py` y montarlo en `app/api/v1/router.py` bajo prefix `/public` (rutas `/api/v1/public/*`); verificar que `openspec`/import no rompe (`python -c "import app.main"` desde `backend/`).
- [x] 1.3 Implementar `GET /api/v1/public/profesionales` (lista de `{id, nombre}` activos, sin auth) en `public/router.py`; verificar con test HTTP que responde 200 y lista.

## 2. Backend — cálculo de slots (TDD)

- [x] 2.1 Escribir tests RED en `backend/test/test_public_slots.py` para `generar_inicios` (casos borde: duración mayor que grilla, slot que no cabe al final) y `slot_libre` (turno cancelado libera, bloqueo excluye, solapamiento por sillón/profesional); verificar que fallan antes de implementar.
- [x] 2.2 Implementar los helpers puros `generar_inicios` y `slot_libre` en `public/service.py` reusando `solapamiento` de `agenda/service.py`; verificar `pytest backend/test/test_public_slots.py` en verde.
- [x] 2.3 Escribir test RED de integración para `PublicReservaService.disponibilidad` (huecos para fecha, profesional específico, lista vacía cuando ocupado) en `backend/test/test_public_service.py`; verificar que falla.
- [x] 2.4 Implementar `PublicReservaService.disponibilidad` orquestando consultas a DB y los helpers puros, con config de jornada laboral; verificar tests en verde.

## 3. Backend — reserva y find-or-create de paciente (TDD)

- [x] 3.1 Escribir test RED para find-or-create de `Paciente` por DNI (existente reutilizado sin duplicado, nuevo creado, actualización de teléfono) en `test_public_service.py`; verificar que falla.
- [x] 3.2 Implementar la lógica find-or-create (incluyendo reactivación de soft-deleted) en `PublicReservaService`; verificar tests en verde.
- [x] 3.3 Escribir tests RED para `reservar`: 201 con turno `reservado` y token, 409 en hueco ocupado, 422 por campos faltantes; verificar que fallan.
- [x] 3.4 Implementar `PublicReservaService.reservar` reusando `TurnoService.crear` (construyendo `TurnoCreate`) y `Paciente` find-or-create; verificar tests en verde y que no se duplica lógica de antisolapamiento.

## 4. Backend — vista y cancelación por token (TDD)

- [x] 4.1 Escribir tests RED para `obtener_por_token` (200 con datos públicos sin IDs/DNI, 404) y `cancelar_por_token` (200 en `reservado`/`confirmado`, 409 en otros estados, 404) en `test_public_service.py`/`test_public_router.py`; verificar que fallan.
- [x] 4.2 Implementar `obtener_por_token` y `cancelar_por_token` en `PublicReservaService` y los endpoints `GET/POST /api/v1/public/turnos/{token}`; verificar tests en verde.

## 5. Backend — schemas, validación y errores

- [x] 5.1 Definir en `public/schemas.py` `PacientePublicoIn`, `ReservaCreate`, `SlotOut`, `PublicTurnoOut` con `extra="forbid"` y constraints (R1); tests de validación (campo extra → 422, obligatorios → 422) en `test_public_schemas.py`; verificar.
- [x] 5.2 Verificar que las respuestas públicas no incluyen `dni`/`telefono`/IDs internos (test en `test_public_router.py`); corregir mapeo si falla.

## 6. Frontend — API tipada y configuración

- [x] 6.1 Crear `frontend/src/shared/api/public.ts` con `getDisponibilidad`, `reservar`, `getTurnoPublico`, `cancelarTurnoPublico`, `listarProfesionalesPublicos` tipadas reusando `request<T>`; verificar `tsc --noEmit`.
- [x] 6.2 Documentar `VITE_WHATSAPP_CONSULTORIO` en `.env.example` y `WHATSAPP_CONSULTORIO`/slots en `backend/.env.example` (si existe) o README; verificar archivos actualizados.

## 7. Frontend — wizard `/reservar`

- [x] 7.1 Implementar `ReservarWizard` con estado tipado y 4 pasos (`PasoPrestacion`, `PasoProfesional`, `PasoHorario`, `PasoDatos`) bajo `features/reserva-publica/`; verificar `npm run lint` y `npm run build`.
- [x] 7.2 Integrar llamadas a `/public/disponibilidad` y `/public/reservar`, navegación a `/p/turno/:token` y manejo de errores 409/422; verificar build sin errores de tipo.
- [x] 7.3 Ajustar `app/router.tsx` para ruta `/reservar` (sin slug) y `/p/turno/:token`; verificar build.

## 8. Frontend — vista `/p/turno/:token`

- [x] 8.1 Implementar `TurnoPublicoPage` mostrando datos del turno, botón "Cancelar turno" y `WhatsappButton` que abre `wa.me` en nueva pestaña con mensaje prearmado; verificar lint+build.
- [x] 8.2 Implementar `WhatsappButton` con sanitización del teléfono y `target="_blank" rel="noopener noreferrer"`; deshabilitar si no hay teléfono configurado; verificar lint+build.

## 9. Integración y verificación final

- [x] 9.1 Aplicar migraciones (`alembic upgrade head` desde `backend/`) y correr `pytest backend/test/test_public_*.py` en verde (incluyendo slot computation y find-or-create).
- [x] 9.2 Ejecutar `npm run lint` y `npm run build` en `frontend/` sin errores; smoke manual del wizard y de `/p/turno/:token`.
- [x] 9.3 Revisar con skill `business-rule-coverage-auditor` la cobertura de RN-AG-06, RN-G-01 y R1/R8/R9/R10/R13 en el change antes de archivar.

## Workflow follow-up

- Archivar el change con `/opsx:archive c-06-reserva-online-publica` y marcar `[x]` en `CHANGES.md` una vez verificado.
- Verificar el resultado archivado.