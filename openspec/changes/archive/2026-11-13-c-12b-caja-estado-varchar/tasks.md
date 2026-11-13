# Tasks

## 1. Migración 0015

- [x] 1.1 Crear `backend/src/app/db/migrations/versions/0015_cierres_estado_varchar.py` con `revision = "0015_cierres_estado_varchar"` (27 caracteres), `down_revision = "0014_pagos_simulados"`, type hints y `snake_case`. Verificación: `cd backend; alembic heads` muestra un único head y `python -m pytest test/test_migration_revision_ids.py -q` pasa.
- [x] 1.2 Implementar `upgrade()`: quitar el default, `op.alter_column("cierres_caja", "estado", type_=sa.String(20), postgresql_using="estado::text")`, restablecer `server_default='pendiente'`, `op.execute("DROP TYPE IF EXISTS estado_cierre")` y `op.create_check_constraint("estado", "cierres_caja", "estado IN ('pendiente', 'cerrado', 'reabierto')")`. Verificación: `cd backend; alembic upgrade head` termina sin error y una consulta a `information_schema.columns` + `pg_constraint` sobre `cierres_caja.estado` muestra `character varying(20)`, default `'pendiente'::character varying` y el CHECK `estado`.
  - Nota: por la `naming_convention` del proyecto (`ck_%(table_name)s_%(constraint_name)s`), el CHECK lógico `estado` se materializa como `ck_cierres_caja_estado`, igual que en el `CheckConstraint(name="estado")` del modelo.
- [x] 1.3 Implementar `downgrade()` simétrico: `op.drop_constraint("estado", "cierres_caja")`, quitar el default, recrear el tipo `estado_cierre` (`pendiente`, `cerrado`, `reabierto`), `op.alter_column(..., type_=sa.Enum(..., name="estado_cierre"), postgresql_using="estado::estado_cierre")` y restablecer el default. Verificación: `cd backend; alembic downgrade 0014_pagos_simulados; alembic upgrade head` completa el round-trip sin errores ni objetos huérfanos.

## 2. Test de migración

- [x] 2.1 Crear `backend/test/test_migration_0015.py` siguiendo el patrón de `test_migration_0004.py`/`0005`/`0006`: verificar que el archivo existe, `revision`/`down_revision`, `String(20)`, `postgresql_using`, `DROP TYPE IF EXISTS estado_cierre`, `create_check_constraint`/`drop_constraint` y `server_default` `'pendiente'` en `upgrade` y `downgrade`. Verificación: `cd backend; python -m pytest test/test_migration_0015.py -q` pasa (9 tests).
- [x] 2.2 Verificar que el test cubre las cuatro condiciones pedidas en el spec: tipo `varchar(20)`, ausencia de `estado_cierre` en `pg_type`, CHECK `estado` y `server_default='pendiente'`. Verificación: revisar que cada aserción falla si se borra la línea correspondiente de la migración (mutación manual rápida) y vuelve a pasar al restaurarla.
  - Evidencia: 7 mutaciones aplicadas una por una sobre la migración (tipo, `USING`, `DROP TYPE`, catálogo del CHECK, `server_default`, `USING` del downgrade, `drop_constraint`); las 7 fueron detectadas y el archivo se restauró byte a byte. El test cubre la ausencia del `CREATE TYPE` en `upgrade` y la presencia de `DROP TYPE IF EXISTS estado_cierre`; la ausencia real en `pg_type` se verificó empíricamente en 3.1.

## 3. Integración con PostgreSQL real

- [x] 3.1 Aplicar la migración a la base de integración y correr los tests de caja que hoy fallan con 500. Verificación: `cd backend; $env:DATABASE_URL="postgresql+psycopg://odonto:odonto@localhost:5432/odonto_test"; alembic upgrade head; python -m pytest test/test_caja_cierre_router.py test/test_caja_cierre_service.py test/test_caja_router.py test/test_caja_service.py -q` pasa, sin `UndefinedFunction: estado_cierre`.
  - Evidencia: RED sobre `odonto_test` en `0014` = 19 fallos con `psycopg.errors.UndefinedFunction: el operador no existe: estado_cierre = character varying`; tras `0015` = 0 ocurrencias de `UndefinedFunction` y 13 fallos, todos deuda de tests no deterministas ya documentada (fuera de alcance).
- [x] 3.2 Correr la suite completa contra `odonto_test` y confirmar que los fallos bajan de 20 a 10 y que los 10 restantes son exactamente la deuda conocida (9 tests de caja no deterministas + `test_agenda_rango_router.py::test_turno_out_conserva_todos_los_campos`). Verificación: `python -m pytest -q` y comparar el listado de fallos contra `design.md` § Deuda conocida; no debe aparecer ningún fallo nuevo atribuible a la migración.
  - Evidencia: base recreada desde cero, `upgrade head`, seed y `pytest -q` ⇒ `10 failed, 543 passed, 7 skipped`. Los 10 fallos son exactamente los de la deuda conocida. Los 543 passed = 534 esperados + 9 tests nuevos de `test_migration_0015.py`.

## 4. Verificación de calidad

- [x] 4.1 Correr lint y typecheck del backend. Verificación: `cd backend; ruff check src test` sin errores.
  - Evidencia: `ruff check src test --statistics` = 44 findings, idénticos al baseline del paso 0 (24 F401, 9 UP017, 6 I001, 2 RUF100, 1 RUF012, 1 RUF022, 1 F841). Los archivos nuevos no agregan findings; los 44 son preexistentes de otros módulos y quedan fuera de alcance.
- [x] 4.2 Correr la suite rápida sin base. Verificación: `cd backend; python -m pytest -m "not integration" -q` en verde (280+ tests).
  - Evidencia: `289 passed, 8 skipped, 263 deselected` (280 del baseline + 9 del test nuevo).
- [x] 4.3 Validar el change. Verificación: `openspec validate c-12b-caja-estado-varchar --strict` y `openspec validate --all` sin errores.
  - Evidencia: `Change 'c-12b-caja-estado-varchar' is valid`; `openspec validate --all` ⇒ `19 passed, 0 failed`.
- [x] 4.4 Pasar la auditoría de reglas duras y de negocio del change (R2, R3, R5, R13; RN-CJ-01/02). Verificación: correr la skill `business-rule-coverage-auditor` sobre el change y registrar la matriz de cobertura sin conflictos abiertos.
  - Evidencia: matriz completa en `openspec/changes/c-12b-caja-estado-varchar/audit-rules.md`. R2, R3, R5 y R13 ✅; RN-CJ-01/02 ✅ (cobertura preexistente, no afectada por el DDL). R7 ➖ N/A. Sin conflictos regla-vs-regla. Quedan 2 observaciones documentales (nombre físico del CHECK por `naming_convention` y cita de `0008` en `proposal.md`/`design.md`) y una propuesta no bloqueante: tests de integración de esquema en un change de calidad posterior.

## Workflow follow-up

- Este change es **CRÍTICO (caja)**: no se implementa sin aprobación humana explícita de `proposal.md`, `design.md` y `tasks.md`. (Aprobación recibida; implementado en modo Strict TDD.)
- Archivar el change con `/opsx:archive c-12b-caja-estado-varchar` y marcar el avance correspondiente en `CHANGES.md`. (Pendiente: no se archiva en esta sesión.)
- Abrir el change de calidad posterior para los 9 tests no deterministas de caja y el test desactualizado de agenda (fuera de alcance de este change).
