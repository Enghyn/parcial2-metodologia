# Tasks

Cwd canónico para todo: `backend/`. Regla TDD: cada grupo tiene su tarea RED (el test falla porque falta la implementación) antes de la tarea GREEN. Integración requiere `docker compose up` + `alembic upgrade head` desde `backend/` ANTES de correr la suite (Postgres con datos de `python -m app.db.seed`). Los tests de helpers puros (grupo 2) corren sin DB.

## 1. Setup estructural

- [x] 1.1 Actualizar `backend/test/test_structure.py`: agregar `agenda` a `MODULOS_CON_RUTAS` y a `MODULOS_SIN_STUBS` (su router deja de estar vacío y sus barrels dejan de ser stubs TODO). Verificación: `pytest test/test_structure.py` en verde.
- [x] 1.2 Montar el router en `backend/src/app/api/v1/router.py` (`include_router(agenda.router)`) con el import correspondiente, dejando el agregador sin romper `test_structure`. Verificación: `python -c "from app.api.v1.router import router; print(len(router.routes))"` no falla y `pytest test/test_structure.py` en verde.

## 2. Helpers puros de solapamiento (TDD, sin DB)

- [x] 2.1 RED — Crear `backend/test/test_agenda_conflicts.py` con casos para `solapamiento(inicio_a, fin_a, inicio_b, fin_b)` (solape verdadero, sin solape, tangencia `fin_a == inicio_b` → falso) y `detectar_conflicto(...)` (None en hueco libre; `"sillon"` por mismo sillón; `"profesional"` por mismo profesional en distinto sillón; `"bloqueo"` por rango bloqueado; cancelado/borrado no cuenta). Verificación RED: `pytest test/test_agenda_conflicts.py` falla porque los helpers no existen.
- [x] 2.2 GREEN — Implementar en `backend/src/app/modules/agenda/service.py` los helpers puros `solapamiento` y `detectar_conflicto` (fórmula exacta RN-AG-01) sin imports de FastAPI ni DB. Verificación: `pytest test/test_agenda_conflicts.py` en verde.

## 3. Schemas Pydantic (TDD)

- [x] 3.1 RED — Crear `backend/test/test_agenda_schemas.py` con casos: `TurnoCreate`/`BloqueoCreate` con `extra="forbid"` rechazan campo extra (422 a nivel schema), campos requeridos faltantes, `duracion_min <= 0` rechazado, `BloqueoCreate` sin `sillon_id` ni `profesional_id` rechazado, `hasta <= desde` rechazado. Verificación RED: `pytest test/test_agenda_schemas.py` falla porque los schemas son stub.
- [x] 3.2 GREEN — Implementar `backend/src/app/modules/agenda/schemas.py`: `TurnoCreate`, `TurnoEstadoUpdate`, `TurnoOut`, `BloqueoCreate`, `BloqueoOut` con `ConfigDict(extra="forbid")`, validadores de bloqueo y normalización de datetimes naive a UTC. Verificación: `pytest test/test_agenda_schemas.py` en verde.

## 4. `TurnoService` (TDD, contra Postgres)

- [x] 4.1 RED — Crear `backend/test/test_agenda_service.py` (patrón auth: sesión real a la base de test) con casos: crear en hueco libre persiste `fin = inicio + duracion_min`; conflicto mismo sillón → HTTPException 409; conflicto mismo profesional distinto sillón → 409; éxito mismo horario con sillón y profesional distintos; éxito sobre turno previamente cancelado; `listar` con filtros fecha/profesional/sillón excluye borrados; `cambiar_estado` de turno inexistente → 404; crear y eliminar bloqueo. Verificación RED: `pytest test/test_agenda_service.py` falla porque el servicio es stub.
- [x] 4.2 GREEN — Implementar `TurnoService` en `service.py`: `listar`, `crear` (cálculo de `fin`, detección de conflicto con turnos y bloqueos, persistencia), `cambiar_estado`, `crear_bloqueo`, `eliminar_bloqueo`, usando `Session` y los helpers puros de D2. Verificación: `pytest test/test_agenda_service.py` en verde.

## 5. Endpoints HTTP (TDD, httpx real)

- [x] 5.1 RED — Crear `backend/test/test_agenda_router.py` con `httpx.AsyncClient` sobre `create_app()` y `dependency_overrides`: los 5 escenarios obligatorios de CHANGES (201 hueco libre, 409 mismo sillón, 409 mismo profesional distinto sillón, éxito mismo horario distinto recurso, éxito sobre cancelado); RBAC 401 sin token y 403 rol insuficiente; 404 turno/bloqueo inexistente; 422 campo extra; bloqueos POST/DELETE. Verificación RED: `pytest test/test_agenda_router.py` falla porque el router está vacío.
- [x] 5.2 GREEN — Implementar `backend/src/app/modules/agenda/router.py`: `GET /turnos`, `POST /turnos`, `PATCH /turnos/{id}/estado`, `POST /bloqueos`, `DELETE /bloqueos/{id}` con `Depends(require_role(...))`, instanciando `TurnoService(db)` y usando los schemas. Verificación: `pytest test/test_agenda_router.py` en verde.

## 6. Integración y cierre

- [x] 6.1 Ejecutar la suite completa desde `backend/` (con Postgres arriba y `alembic upgrade head` aplicado): `pytest` sin errores ni regresiones de C-01/C-02/C-03. Verificación: output de pytest sin fallos.
- [x] 6.2 Trazabilidad de reglas duras: verificar evidencia R1 (`extra="forbid"` en schemas), R2 (cero `tenant_id`), R5 (type hints + snake_case + sin migración), R6 (validación en servicio + test de conflicto), R8 (401/403 server-side), R9 (sin datos sensibles en logs/URLs), R13 (`deleted_at IS NULL` en queries) con test_id por regla. Verificación: checklist en la descripción del PR del change.

## Workflow follow-up

- Ejecutar `/opsx:validate` y `/opsx:archive c-04-agenda-servicio-antisolapamiento` cuando las 6 tareas estén en verde y el change sea revisado.
- Marcar `[x]` la sección C-04 en `CHANGES.md` tras el archive.
- Avisar a C-05 y C-06 que `TurnoService`, los helpers puros y los endpoints quedan listos (contrato en `design.md` D2/D4/D8).