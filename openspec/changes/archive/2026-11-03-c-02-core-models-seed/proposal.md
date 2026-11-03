# Proposal — C-02 core-models-seed

## Why

La fundación (C-01) dejó un backend FastAPI que arranca, responde salud y tiene Alembic inicializado, pero **sin una sola tabla de dominio**. Todo lo que sigue —login con roles, agenda con antisolapamiento, ficha clínica y caja— necesita un esquema canónico y datos mínimos para poder existir.

Sin C-02 no hay contrato de datos: cada change inventaría sus propias tablas, tipos y convenciones, y las reglas de negocio (borrado lógico, caja inmutable, integridad de turnos) quedarían dispersas o ausentes. C-02 fija ese contrato una sola vez, en una migración versionada y con un seed reproducible.

## What Changes

- **Nueve modelos SQLAlchemy 2.0** en `backend/src/app/modules/*/models.py`, todos registrados sobre la misma `Base`:
  `Usuario`, `Sillon`, `Profesional`, `Paciente`, `Turno`, `Bloqueo`, `Odontograma`, `HallazgoPieza`, `MovimientoCaja`.
- **Migración Alembic `0002_core_models`**, encadenada a `0001_baseline`, que crea tablas, constraints e índices en PostgreSQL.
- **Seed idempotente** (`backend/src/app/db/seed.py` + comando ejecutable): 3 sillones, 1 admin, 1 recepcionista, 2 odontólogos y 2 pacientes de prueba.
- **Constraints de integridad en el modelo**: unicidad de `email`, `dni`, `token_publico` y `matricula`; `CHECK` de rangos (monto > 0, `fin > inicio`, pieza FDI válida); borrado lógico con `deleted_at` en las cuatro entidades de negocio.
- **Caja append-only**: `MovimientoCaja` no expone actualización ni borrado; los errores se compensan con un contra-asiento.
- **Tests sin PostgreSQL vivo** (metadata de SQLAlchemy + inspección estática de la migración + seed testeado con repositorio falso), más un test de integración opcional que se saltea si no hay DSN.

## Capabilities

### New Capabilities

- `core-data-model`: contrato de persistencia del consultorio mono-tenant. Cubre el esquema creado por migración, la integridad declarada (PK/FK/unique/check/índices), el borrado lógico, la inmutabilidad de caja y el seed idempotente.

### Modified Capabilities

- Ninguna. `backend-foundation` ya cubre arranque, salud, configuración, errores, logging y el baseline Alembic; C-02 agrega comportamiento nuevo en una capacidad propia y no cambia requisitos existentes.

## Impact

- **Código backend**: `backend/src/app/modules/{admin,agenda,clinica,caja}/models.py` (modelos reales), `backend/src/app/db/base.py` (convenciones de metadata), `backend/src/app/db/seed.py` (nuevo), `backend/src/app/db/migrations/versions/0002_core_models.py` (nuevo).
- **Dependencias**: se agrega `bcrypt>=4.1` a `backend/pyproject.toml` para que el seed guarde hashes reales de contraseñas de demo; C-03 reutiliza la misma librería para verificar el login. Sin servicios externos ni Redis.
- **Tests**: nuevos `backend/test/test_models_structure.py`, `test_migration_0002.py` y `test_seed.py`.
- **API**: sin endpoints nuevos. C-02 es capa de persistencia; los routers siguen en stub.
- **Datos**: el seed es de desarrollo/demostración y no corre automáticamente en producción.
- **No incluye**: hashing de login, JWT/RBAC, validación de antisolapamiento en servicios (C-04), endpoints de pacientes/agenda/caja, ni cambios de frontend.
