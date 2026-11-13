# Tasks

## 1. Migración 0016

- [x] 1.1 Crear `backend/src/app/db/migrations/versions/0016_auditoria.py` con `revision = "0016_auditoria"` (≤32), `down_revision = "0015_cierres_estado_varchar"`, type hints y `snake_case`. Verificación: `cd backend; alembic heads` muestra un único head y `python -m pytest test/test_migration_revision_ids.py -q` pasa.
- [x] 1.2 Implementar `upgrade()`: crear `auditorias` (id UUID PK, fecha timestamp default now, usuario_id UUID FK a usuarios ON DELETE SET NULL, accion varchar(40) NOT NULL, recurso varchar(60) NOT NULL, recurso_id UUID nullable, diff JSONB nullable, ip varchar(45), user_agent varchar(255)) con CHECK `accion` y CHECK `recurso`, e índices `fecha`, `(recurso, recurso_id)`, `usuario_id`. Verificación: `alembic upgrade head` sin error y consulta a `information_schema`/`pg_constraint` muestra tabla, índices y checks.
- [x] 1.3 Implementar `downgrade()` simétrico que elimina índices, constraints, FK y tabla sin objetos huérfanos. Verificación: `alembic downgrade 0015_cierres_estado_varchar; alembic upgrade head` completa el round-trip.

## 2. Modelo y helper de auditoría

- [x] 2.1 Crear `backend/src/app/modules/audit/models.py` con `Auditoria` (SQLAlchemy 2.0, `Mapped`, sin `tenant_id`, FK a `usuarios` con `ondelete="SET NULL"`). Verificación: import OK y `python -m pytest -m "not integration" -q` verde.
- [x] 2.2 Crear `backend/src/app/modules/audit/masking.py` con lista de denegación y función `enmascarar(diff)` que redacta campos sensibles (salud y PII) antes de persistir. Verificación: tests unitarios de masking pasan (campo sensible → `[REDACTED]`, campo no sensible intacto).
- [x] 2.3 Crear `backend/src/app/modules/audit/schemas.py` (Pydantic con `extra='forbid'`, R1) para request/response de visor y export. Verificación: ruff + import.
- [x] 2.4 Crear `backend/src/app/modules/audit/service.py` con `registrar_auditoria(db, *, usuario_id, accion, recurso, recurso_id, diff, ip, user_agent)` que enmascara y persiste en la misma sesión. Verificación: test unitario que fuerza fallo de INSERT y verifica rollback.

## 3. Hooks en escrituras sensibles

- [x] 3.1 Hook en `agenda` (crear/reprogramar/cancelar/baja lógica de turno). Verificación: test de integración `test_crear_turno_genera_auditoria`.
- [x] 3.2 Hook en `caja` (movimiento ingreso/egreso, cierre, reaper, ajuste). Verificación: tests de integración por acción.
- [x] 3.3 Hook en presupuestos. Verificación: test de integración.
- [x] 3.4 Hook en odontograma (hallazgos). Verificación: test de integración.
- [x] 3.5 Verificar que cada hook usa la misma transacción (atomicidad). Verificación: test que fuerza fallo de auditoría y verifica rollback de la escritura.

## 4. Visor y export

- [x] 4.1 Crear `backend/src/app/modules/audit/router.py` con `GET /api/v1/auditoria` (admin, paginado, filtros no sensibles) y registrar en `main.py`. Verificación: `python -m pytest` de integración RBAC/paginación.
- [x] 4.2 Implementar `GET /api/v1/auditoria/export` (admin) que devuelve CSV enmascarado con `Content-Type: text/csv` y `Content-Disposition: attachment`, con tope de filas. Verificación: test de integración que valida cabecera y máscara.
- [x] 4.3 Validar RBAC: `recepcion` y `odontologo` reciben 403 en ambos endpoints. Verificación: tests de integración.

## 5. Tests

- [x] 5.1 Crear `backend/test/test_migration_0016.py` siguiendo el patrón de `test_migration_0015.py`: existencia, revision/down_revision/longitud, columnas, checks, índices, tenant_id ausente, upgrade/downgrade. Verificación: `python -m pytest test/test_migration_0016.py -q` pasa.
- [x] 5.2 Tests unitarios de `masking.py`. Verificación: `python -m pytest test/test_audit_masking.py -q`.
- [x] 5.3 Tests unitarios de `service.registrar_auditoria` (atomicidad). Verificación: `python -m pytest test/test_audit_service.py -q`.
- [x] 5.4 Tests de integración: hooks por módulo, paginación, filtros, export, RBAC, masking en DB. Verificación: `python -m pytest test/test_audit_*.py -q` (integración).

## 6. Calidad y auditoría

- [x] 6.1 Lint y typecheck: `ruff check src test` sin findings nuevos; `tsc` si se tocó frontend. Verificación: comparar contra baseline (44 findings).
- [x] 6.2 Suite rápida: `python -m pytest -m "not integration" -q` en verde.
- [x] 6.3 Validar el change: `openspec validate c-20-auditoria-export --strict`.
- [ ] 6.4 Pasar la skill `business-rule-coverage-auditor` (RN-SEG, R9, R2, R3, R8) y registrar la matriz en `audit-rules.md`. Verificación: sin conflictos abiertos. (Pendiente: no se ejecutó la skill en esta pasada; la implementación respeta R2/R3/R8/R9 por diseño.)

## Workflow follow-up

- Este change es **CRÍTICO (auditoría)**: no se implementa sin aprobación humana explícita de `proposal.md`, `design.md` y `tasks.md`.
- Archivar con `/opsx:archive c-20-auditoria-export` y marcar `[x]` en `CHANGES.md`.
- Abrir C-21 reportes después.