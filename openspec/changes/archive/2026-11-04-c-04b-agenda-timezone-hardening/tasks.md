# Tasks — C-04b agenda timezone hardening

> **TDD estricto.** Comandos backend desde `backend/`. La suite completa requiere PostgreSQL migrado y sembrado (ver `AGENTS.md`).

## 1. Safety net y RED de timezone

- [x] 1.1 Correr `python -m pytest -q` con `DATABASE_URL` apuntando a una base migrada/sembrada y registrar la línea base (esperado: 211 passed, 7 skipped).
- [x] 1.2 Crear `backend/test/test_timezone.py` con tests que fallen: `09:00 ART = 12:00Z`, `inicio_dia(2027-01-10) = 2027-01-10T00:00-03:00`, `normalizar_entrada(naive)` devuelve ART.

## 2. Helper de zona canónica

- [x] 2.1 **GREEN**: crear `backend/src/app/core/timezone.py` con `TZ_CONSULTORIO`, `ahora`, `inicio_dia`, `fin_dia`, `combinar` y `normalizar_entrada`; verificar `test_timezone.py`.
- [x] 2.2 **TRIANGULATE**: agregar casos de borde 00:00, 23:59 y cambio de día; verificar que no hay conversiones dobles.
- [x] 2.3 **REFACTOR**: dejar el helper sin dependencias de FastAPI/SQLAlchemy; correr `ruff` sobre el archivo.

## 3. Agenda interna: día ART y naive ART

- [x] 3.1 **RED**: ampliar `test_agenda_service.py` y `test_agenda_schemas.py` con: filtro `fecha` ART (incluye 22:00 ART, excluye 23:00 del día anterior), naive 09:00 → 12:00Z, `fin` calculado sobre el instante correcto.
- [x] 3.2 **GREEN**: actualizar `agenda/schemas.py` (`_a_utc` → normalización ART) y `agenda/service.py::listar` (`inicio_dia`/`fin_dia`); verificar verde.
- [x] 3.3 **TRIANGULATE**: agregar un turno a las 22:00 ART y verificar que aparece en el día correcto y no en el siguiente.
- [x] 3.4 **REFACTOR**: eliminar `timezone.utc` de los archivos tocados; correr `ruff`.

## 4. Reserva pública: slots ART y slots pasados

- [x] 4.1 **RED**: actualizar `test_public_service.py` y `test_public_slots.py` para esperar slots ART (09:00 ART = 12:00Z) y para verificar que un slot ya pasado no se devuelve.
- [x] 4.2 **GREEN**: actualizar `public/service.py::disponibilidad` (`inicio_dia`/`fin_dia`/`combinar`/`ahora`) y `public/schemas.py` (naive ART); verificar verde.
- [x] 4.3 **TRIANGULATE**: agregar el caso “todo el día ya pasó” → lista vacía y el caso “slot a las 20:00 ART” incluido si es futuro.
- [x] 4.4 **REFACTOR**: reusar los helpers de agenda (`solapamiento`) sin duplicar lógica; correr la suite pública.

## 5. Recursos vigentes y fechas futuras

- [x] 5.1 **RED**: agregar a `test_agenda_service.py`/`test_agenda_router.py` casos de sillón borrado, profesional inactivo, paciente borrado y `inicio` pasado; verificar que fallan.
- [x] 5.2 **GREEN**: implementar en `TurnoService.crear` la validación de recursos y `inicio > ahora()`; verificar que responden 404/422.
- [x] 5.3 **TRIANGULATE**: agregar el caso feliz con recursos activos y el caso `inicio` futuro; verificar 201.
- [x] 5.4 **REFACTOR**: extraer un helper `_recurso_vigente(model, id, nombre)`; correr `ruff`.

## 6. Frontend en ART

- [x] 6.1 **RED/verificación**: actualizar `features/agenda/dateUtils.ts` (`formatHora` con `timeZone: "America/Argentina/Buenos_Aires"`, `toIsoDate` y `localInputToUtc` en ART) y `features/reserva-publica/types.ts` (eliminar `formatHoraUtc`/`formatFechaUtc`); verificar que `tsc` falla si quedan imports rotos.
- [x] 6.2 **GREEN**: actualizar `TurnoModal.tsx` para usar `localInputToUtc`, `PasoHorario.tsx` y `TurnoPublicoPage.tsx` para usar los formateadores ART; verificar `npm run lint` y `npx tsc --noEmit`.
- [x] 6.3 **TRIANGULATE**: revisar que la agenda interna y el portal muestren `09:00` para el mismo `12:00Z`; documentar la verificación manual si no hay runner.
- [x] 6.4 **REFACTOR**: centralizar el string de zona en una constante exportada; correr `npm run build`.

## 7. Verificación integral

- [x] 7.1 Correr `python -m pytest -q` con PostgreSQL y confirmar toda la suite en verde.
- [x] 7.2 Correr `python -m ruff check src test` (los errores preexistentes de C-03..C-06 se resuelven en `chore-quality-gate`; este change no debe agregar nuevos).
- [x] 7.3 Correr `npm run lint`, `npx tsc --noEmit` y `npm run build`.
- [x] 7.4 Ejecutar `openspec validate "c-04b-agenda-timezone-hardening" --strict`.

## Workflow follow-up

- Revisión humana de las decisiones de `design.md` antes de aplicar.
- Aplicar con TDD y actualizar los checkboxes.
- Archivar con `openspec archive "c-04b-agenda-timezone-hardening" -y`.
- Continuar con `c-06b-public-patient-privacy` y `chore-quality-gate`.
