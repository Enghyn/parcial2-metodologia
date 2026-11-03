# Tasks — C-02b core-data-model-hardening

> **Modo TDD estricto.** Cada grupo implementa sus tests y su documentación. Comandos de test desde `backend/` (cwd canónico).

## 1. Preparación y pre-check

- [x] 1.1 Correr `python -m pytest -q` y registrar la línea base (esperado: 74 passed, 2 skipped); verificar que no hay cambios sin commitear.
- [x] 1.2 Ejecutar los pre-checks en PostgreSQL (`email <> lower(btrim(email))`, `length(btrim(motivo)) = 0`, `fin <> inicio + duracion_min * interval '1 minute'`); si hay filas inconsistentes, detenerse y reportarlas antes de migrar.

## 2. Email canónico y case-insensitive

- [x] 2.1 **RED**: agregar a `test_models_structure.py` el test `test_email_se_normaliza_y_es_case_insensitive` (validador `strip+lower`) y la aserción de `ck_usuarios_email_normalizado` en metadata; verificar que falla.
- [x] 2.2 **GREEN**: implementar `@validates("email")` en `Usuario` y el `CheckConstraint("email = lower(btrim(email))", name="email_normalizado")`; verificar que pasa.
- [x] 2.3 **TRIANGULATE**: agregar casos `"  Admin@Consultorio.COM  "`, `"ADMIN@X.COM"` y un email ya canónico; verificar que el valor persistido siempre es minúscula sin espacios.
- [x] 2.4 **REFACTOR**: extraer el helper de normalización si se repite; correr la suite de modelos.

## 3. Motivo de bloqueo no vacío

- [x] 3.1 **RED**: agregar a `test_models_structure.py` la aserción de `ck_bloqueos_motivo_no_vacio` y un caso con `motivo=""`/`"   "`; verificar que falla.
- [x] 3.2 **GREEN**: agregar `CheckConstraint("length(btrim(motivo)) > 0", name="motivo_no_vacio")` en `Bloqueo`; verificar verde.
- [x] 3.3 **TRIANGULATE**: agregar el caso `motivo="Feriado"` aceptado; verificar que el constraint no bloquea valores válidos.
- [x] 3.4 **REFACTOR**: revisar nombres y orden de `__table_args__`; correr la suite.

## 4. Coherencia `fin`/`duracion_min`

- [x] 4.1 **RED**: agregar a `test_models_structure.py` la aserción de `ck_turnos_fin_coherente` y un caso `inicio=10:00, duracion=30, fin=10:45`; verificar que falla.
- [x] 4.2 **GREEN**: agregar `CheckConstraint("fin = inicio + (duracion_min * interval '1 minute')", name="fin_coherente")` en `Turno`; verificar verde.
- [x] 4.3 **TRIANGULATE**: agregar el caso coherente (`fin=10:30`) y otro con `duracion=45`; verificar ambos.
- [x] 4.4 **REFACTOR**: documentar en el docstring del modelo que C-04 debe calcular `fin` con la misma fórmula; correr la suite.

## 5. Migración `0003` con constraints y triggers

- [x] 5.1 **RED**: crear `test_migration_0003.py` que exija `revision="0003_core_data_model_hardening"`, `down_revision="0002_core_models"`, los tres `CHECK`, las dos funciones y los diez triggers; verificar que falla.
- [x] 5.2 **GREEN**: crear `backend/src/app/db/migrations/versions/0003_core_data_model_hardening.py` con `ALTER TABLE ... ADD CONSTRAINT` (SQL explícito), `fn_forbid_ledger_mutation`, `fn_forbid_physical_delete`, triggers `BEFORE UPDATE OR DELETE`/`BEFORE DELETE` y `BEFORE TRUNCATE`; verificar verde.
- [x] 5.3 **TRIANGULATE**: agregar al test la verificación del downgrade (10 `DROP TRIGGER`, 2 `DROP FUNCTION`, 3 `DROP CONSTRAINT`) y que no toque tablas ni `btree_gist`; corregir hasta verde.
- [x] 5.4 **REFACTOR**: ordenar funciones/triggers y comentar el propósito de cada bloque; verificar `alembic upgrade head --sql` sin base.

## 6. Seed con error operativo claro

- [x] 6.1 **RED**: agregar a `test_seed.py` `test_main_sin_base_devuelve_1_y_mensaje_claro` con `monkeypatch` de `get_session_factory` que lanza `OperationalError`; verificar que falla.
- [x] 6.2 **GREEN**: modificar `main()` para capturar `SQLAlchemyError`, hacer rollback, imprimir el mensaje accionable por `stderr` y devolver `1`; verificar verde.
- [x] 6.3 **TRIANGULATE**: agregar un caso con sesión falsa que falla a mitad de `apply_seed`; verificar que se llama `rollback()` y `close()` y que no se commitea nada.
- [x] 6.4 **REFACTOR**: mantener el `except Exception` para errores de lógica; correr la suite.

## 7. Cobertura RN-CJ-01

- [x] 7.1 Agregar a `test_models_structure.py::test_movimientos_caja` las aserciones de `fecha`, `tipo`, `medio_pago`, `monto`, `concepto` y `usuario_id` no nulos; verificar que pasan (test de caracterización: el código ya cumple, faltaba la verificación).
- [x] 7.2 Agregar a `test_caja_inmutable.py` un caso que construya un movimiento sin `concepto` y verifique que el `NOT NULL` está declarado en metadata.

## 8. Integración PostgreSQL y documentación

- [x] 8.1 Crear `backend/test/test_pg_hardening.py` con `pytest.mark.skipif` cuando no hay `DATABASE_URL`: email con mayúsculas rechazado, motivo vacío rechazado, `fin` incoherente rechazado, `UPDATE`/`DELETE`/`TRUNCATE` de caja rechazados y `DELETE`/`TRUNCATE` de entidades de negocio rechazados.
- [x] 8.2 Ejecutar `8.1` contra la instancia temporal `127.0.0.1:5433` y registrar el resultado; si no hay base, dejar el skip documentado.
- [x] 8.3 En `CHANGES.md`, agregar a C-04, C-07 y C-08 el criterio “toda consulta activa filtra `deleted_at IS NULL`”.
- [x] 8.4 En `knowledge-base/10_preguntas_abiertas.md`, registrar: catálogo `Prestacion` vs duración manual, momento de deducción de la seña y aceptación de triggers en producción.
- [x] 8.5 Correr `python -m pytest -q`, `python -m ruff check src test` y `openspec validate "c-02b-core-data-model-hardening" --strict`.

## Workflow follow-up

- Revisión humana de las cinco decisiones de `design.md` antes de aplicar (gobernanza CRÍTICA).
- Aplicar con TDD y actualizar los checkboxes.
- Archivar con `openspec archive "c-02b-core-data-model-hardening" -y` cuando la verificación esté completa.
- Verificar que `openspec list` vuelve a estar vacío y que la spec `core-data-model` quedó actualizada.
