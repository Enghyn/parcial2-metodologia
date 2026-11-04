# Proposal — C-04: agenda-servicio-antisolapamiento

## Why

C-02 dejó el esquema (`turnos`, `bloqueos`, `sillones`, `profesionales`, `pacientes`) y C-03 dejó el RBAC reutilizable, pero todavía no existe ninguna lógica de negocio ni endpoint que gestione la agenda: no hay validación de antisolapamiento (RN-AG-01), no se calcula `fin` desde `duracion_min` (RN-AG-02) y los stubs `modules/agenda/{schemas,service,router}.py` están vacíos. C-05 (agenda interna) y C-06 (reserva pública) dependen de esta capa para no duplicar reglas; por eso hay que cerrarla ahora, con TDD y una suite de conflicto obligatoria (R6).

## What Changes

- Nuevo módulo `backend/src/app/modules/agenda/` con:
  - `TurnoService` (capa de servicios, KB 08): creación y consulta de turnos con validación cruzada de antisolapamiento (sillón O profesional ocupado en el rango → 409), exclusión de turnos `cancelado` y filtrado `deleted_at IS NULL` (R13/RN-SEG-02), cálculo automático `fin = inicio + duracion_min` (RN-AG-02).
  - CRUD de turnos: `GET /api/v1/turnos` (filtros `fecha`, `profesional_id`, `sillon_id`), `POST /api/v1/turnos`, `PATCH /api/v1/turnos/{id}/estado`.
  - Bloqueos: `POST /api/v1/bloqueos`, `DELETE /api/v1/bloqueos/{id}` (bloqueo tratado como ocupación, RN-AG-04).
- Montaje del router de agenda en `app/api/v1/router.py` (junto a auth).
- Schemas Pydantic con `extra="forbid"` (R1) para toda entrada/salida de la agenda.
- RBAC vía `Depends(require_role(...))` (R8): crear/reprogramar turnos y bloqueos solo `admin`/`recepcion`; cambio de estado también `odontologo`; listado por los tres roles.
- Suite pytest TDD: hueco libre (201), solapamiento mismo sillón (409), solapamiento mismo profesional en distinto sillón (409), mismo horario con sillón y profesional distintos (éxito), creación sobre turno cancelado previo (éxito). Test de conflicto obligatorio (R6).
- Sin migración Alembic nueva: `Bloqueo` ya existe en el esquema de C-02 (sin `deleted_at`, borrado físico permitido por R13 que solo protege `Paciente`/`Turno`/`Profesional`/`Sillon`); `Turno` ya tiene los índices y la restricción `ck_turnos_fin_coherente`. La duración queda manual (`duracion_min`) por decisión cerrada en KB 10 (no hay catálogo `Prestacion` en el MVP).

## Capabilities

### New Capabilities

- `agenda`: Contrato de servicio y HTTP de la agenda de turnos y bloqueos: anti-solapamiento cruzado (RN-AG-01), cálculo de `fin` (RN-AG-02), estados del turno (RN-AG-05), bloqueos como ocupación (RN-AG-04), filtrado `deleted_at IS NULL` (R13/RN-SEG-02) y RBAC de los endpoints internos.

### Modified Capabilities

- (ninguna — la persistencia de `Turno`/`Bloqueo` ya está cubierta por `core-data-model`; este change agrega comportamiento de servicio/HTTP encima, sin alterar requisitos de esquema).

## Impact

- **Código**: `backend/src/app/modules/agenda/{schemas,service,router}.py` (reemplazan los stubs TODO(C-04)); una línea en `app/api/v1/router.py` para `include_router(agenda.router)`; `core/errors` reutilizado (409/404/422).
- **Dependencias**: sin nuevas (reusa FastAPI/SQLAlchemy/Pydantic ya instaladas). `get_current_user`/`require_role` de C-03.
- **Tests**: nuevos `backend/test/test_agenda_service.py` y `backend/test/test_agenda_router.py`; `test_structure.py` deja de considerar agenda como stub (agenda pasa a tener rutas reales).
- **Consumidores futuros**: C-05 (agenda frontend) y C-06 (reserva pública) consumen `TurnoService`; C-07/C-08 reusan el filtrado por `deleted_at` y el patrón de servicio.