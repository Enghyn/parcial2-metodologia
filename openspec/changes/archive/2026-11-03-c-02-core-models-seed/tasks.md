# Tasks — C-02 core-models-seed

> **Modo TDD estricto.** Cada tarea de implementación sigue RED → GREEN → TRIANGULATE → REFACTOR y declara cómo se verifica. Comandos de test desde `backend/` (cwd canónico, `testpaths = ["test"]`, `pythonpath = ["src"]`).
>
> **Gobernanza CRÍTICA:** no aplicar hasta que la tabla “Decisiones para revisión humana” de `design.md` esté aprobada.

## 1. Preparación del contrato de datos

- [x] 1.1 Agregar `bcrypt>=4.1` a `backend/pyproject.toml` e instalar el entorno; verificar con `python -c "import bcrypt; print(bcrypt.__version__)"` desde `backend/`.
- [x] 1.2 Definir la convención de nombres de constraints (`ix_`, `uq_`, `ck_`, `fk_`) en `backend/src/app/db/base.py` y crear `backend/src/app/db/registry.py` que importe `Base` y los nueve modelos; verificar con `python -c "import sys; sys.path.insert(0,'backend/src'); from app.db.registry import Base; print(len(Base.metadata.tables))"` desde la raíz (debe imprimir `9` al final del grupo 6).

## 2. Identidad y recursos: `Usuario`, `Sillon`, `Profesional`

- [x] 2.1 **Safety net + RED**: correr `python -m pytest test/test_structure.py test/test_migrations.py -q` y registrar la línea base; crear `backend/test/test_models_structure.py` con tests que fallen para las tablas `usuarios`, `sillones` y `profesionales` (existencia, PK UUID, columnas, nulos, `uq_usuarios_email`, `uq_profesionales_matricula`); verificar que fallan por ausencia de los modelos.
- [x] 2.2 **GREEN**: implementar lo mínimo de `Usuario`, `Sillon` y `Profesional` en `app/modules/admin/models.py` y `app/modules/agenda/models.py`; verificar que los tests nuevos y la safety net pasan.
- [x] 2.3 **TRIANGULATE**: agregar casos de borde — email normalizado a minúsculas, rol fuera de `('admin','recepcion','odontologo')` con `CHECK` declarado, `usuario_id` único y nullable, `duracion_default_min > 0` — y generalizar el código hasta que pasen.
- [x] 2.4 **REFACTOR**: extraer constantes de enums y el mixin de timestamps reutilizable; correr toda la suite de modelos y confirmar verde.

## 3. Ficha clínica: `Paciente`, `Odontograma`, `HallazgoPieza`

- [x] 3.1 **RED**: ampliar `test_models_structure.py` con tests que fallen para las tres tablas (FK a paciente, `paciente_id` único en odontograma, `CHECK` FDI con posición 1–8 y cuadrante 1–4, `uq_hallazgos_pieza_odontograma_pieza`, enum de estados clínicos).
- [x] 3.2 **GREEN**: implementar los tres modelos en `app/modules/clinica/models.py`; verificar que los tests nuevos pasan.
- [x] 3.3 **TRIANGULATE**: agregar casos `pieza=19`, `pieza=20`, `pieza=49` rechazados y `pieza=11`/`48` aceptados (a nivel de constraint declarado), más `fecha` de tipo `Date`; ajustar hasta verde.
- [x] 3.4 **REFACTOR**: unificar la tupla de estados clínicos entre modelo y test; correr la suite completa.

## 4. Agenda: `Turno` y `Bloqueo`

- [x] 4.1 **RED**: ampliar `test_models_structure.py` con tests que fallen para `turnos` y `bloqueos` (FKs obligatorias, `CHECK fin > inicio`, `duracion_min > 0`, `token_publico` único, enum de estados, `CHECK` de bloqueo con al menos un recurso y `hasta > desde`, índices `(sillon_id, inicio, fin)` y `(profesional_id, inicio, fin)`).
- [x] 4.2 **GREEN**: implementar `Turno` y `Bloqueo` en `app/modules/agenda/models.py` con sus índices y constraints; verificar que los tests nuevos pasan.
- [x] 4.3 **TRIANGULATE**: agregar casos de estado inválido, `token_publico` repetido y bloqueo sin recurso; verificar que el `CHECK` correspondiente está declarado en metadata.
- [x] 4.4 **REFACTOR**: extraer la tupla de estados de turno y los nombres de índices; correr la suite completa.

## 5. Borrado lógico transversal

- [x] 5.1 **RED**: crear tests que fallen en `backend/test/test_soft_delete.py` — `deleted_at` existe y es nullable en `pacientes`, `turnos`, `profesionales` y `sillones`; la guarda lanza excepción al intentar borrar esas entidades; las demás tablas no exponen `deleted_at`.
- [x] 5.2 **GREEN**: implementar el mixin `SoftDeleteMixin` y la guarda `before_delete` (registrada por clase) en `app/db/base.py`; aplicarlo a las cuatro entidades; verificar verde.
- [x] 5.3 **TRIANGULATE**: agregar el caso “borrado lógico setea timestamp y conserva la fila” con una sesión/fixture falsa y el caso “entidad sin mixin no se ve afectada”; ajustar hasta verde.
- [x] 5.4 **REFACTOR**: centralizar el mensaje de error y el registro de guardas; correr la suite completa.

## 6. Caja: `MovimientoCaja` append-only

- [x] 6.1 **RED**: crear `backend/test/test_caja_inmutable.py` con tests que fallen — tabla y columnas, `CHECK monto > 0`, `usuario_id` obligatorio, enums de `tipo` y `medio_pago`, `usuario_id` en metadata, y la guarda que rechaza `before_update`/`before_delete` con `ImmutableLedgerError`.
- [x] 6.2 **GREEN**: implementar `MovimientoCaja` en `app/modules/caja/models.py`, el error en `app/core/errors.py` y los listeners de inmutabilidad; verificar verde.
- [x] 6.3 **TRIANGULATE**: agregar el caso de contra-asiento (dos movimientos de tipo opuesto conservan ambos registros) y el caso de movimiento sin `turno_id`; ajustar hasta verde.
- [x] 6.4 **REFACTOR**: extraer las tuplas de `tipo`/`medio_pago` y el helper de guarda; verificar `len(Base.metadata.tables) == 9` y correr la suite completa.

## 7. Migración Alembic `0002_core_models`

- [x] 7.1 **RED**: crear `backend/test/test_migration_0002.py` con tests que fallen — existe un archivo de versión con `down_revision = "0001_baseline"`, y las tablas creadas coinciden con `Base.metadata.tables`.
- [x] 7.2 **GREEN**: generar/escribir `app/db/migrations/versions/0002_core_models.py` con las nueve tablas, constraints nombrados e índices; verificar que los tests de migración pasan.
- [x] 7.3 **TRIANGULATE**: agregar verificaciones de `downgrade` (dropea las nueve tablas y no `btree_gist`), de los `CHECK`/`UNIQUE` nombrados y de los índices de agenda; corregir hasta verde.
- [x] 7.4 **REFACTOR**: ordenar imports y constantes de la migración; verificar con `alembic upgrade head --sql` (modo offline, sin base) que el SQL contiene los nueve `CREATE TABLE`.
- [x] 7.5 Ejecutar `alembic upgrade head` + `alembic downgrade 0001_baseline` contra PostgreSQL 17 real (instancia temporal en `127.0.0.1:5433`): upgrade crea las 9 tablas, downgrade las elimina y conserva `btree_gist`, re-upgrade + seed deja 3/4/2/2.

## 8. Seed idempotente

- [x] 8.1 **RED**: crear `backend/test/test_seed.py` con tests que fallen — `build_seed_plan()` devuelve 3 sillones, 4 usuarios, 2 profesionales y 2 pacientes con claves naturales únicas y hashes bcrypt válidos; `apply_seed()` con sesión falsa no duplica en una segunda ejecución.
- [x] 8.2 **GREEN**: implementar `backend/src/app/db/seed.py` (`build_seed_plan`, `apply_seed`, `SeedReport`, `__main__`) resolviendo por `email`, `matricula`, `dni` y nombre de sillón; verificar verde.
- [x] 8.3 **TRIANGULATE**: agregar casos de base parcialmente poblada, override de contraseña por `SEED_DEFAULT_PASSWORD` y guarda que rechaza `APP_ENV=production` sin `--force`; ajustar hasta verde.
- [x] 8.4 **REFACTOR**: separar datos de Demo de la lógica de aplicación; correr la suite completa.
- [x] 8.5 Documentar en `README.md` el comando `python -m app.db.seed`, los conteos esperados y las credenciales de demo; verificar que el comando documentado coincide con `--help` del módulo.

## 9. Integración y cierre técnico

- [x] 9.1 Correr `python -m pytest -q` desde `backend/` y confirmar toda la suite en verde (incluye safety net de C-01).
- [x] 9.2 Correr `python -m ruff check src test` desde `backend/` sin errores.
- [x] 9.3 Corregir los docstrings de stubs que digan `core-models-tenancy` y verificar que `Select-String -Path backend/src/app/modules/*/models.py -Pattern "core-models-tenancy"` no devuelve resultados.
- [x] 9.4 Ejecutar `openspec validate "c-02-core-models-seed" --strict` y confirmar `0` errores.
- [x] 9.5 Registrar en el resumen de apply si la verificación con Postgres real quedó pendiente por falta de Docker.

## Workflow follow-up

- Revisión humana de la tabla de decisiones de `design.md` (gobernanza CRÍTICA) antes de aplicar.
- Aplicar el change con TDD, actualizando los checkboxes al completar cada tarea.
- Archivar con `openspec archive "c-02-core-models-seed" -y` una vez verificado.
- Marcar `C-02` como `[x]` en `CHANGES.md` y verificar que `openspec list` vuelve a estar vacío.
