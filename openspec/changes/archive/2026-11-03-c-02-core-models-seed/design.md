# Design — C-02 core-models-seed

## Context

Ver `proposal.md` — Why. El backend ya tiene FastAPI, `pydantic-settings`, SQLAlchemy 2.0 sincrónico (`app/db/session.py`), Alembic con `script_location = src/app/db/migrations` y un baseline (`0001_baseline`) que solo habilita `btree_gist`. Los nueve modelos viven hoy como stubs vacíos en `app/modules/*/models.py` y la `Base` declarativa no registra ninguna tabla.

Restricciones que condicionan el diseño:

- `AGENTS.md` R2: mono-consultorio, sin `tenant_id`.
- `AGENTS.md` R13 / RN-SEG-02: borrado lógico en `Paciente`, `Turno`, `Profesional`, `Sillon`.
- `AGENTS.md` R3 / RN-CJ-02: caja append-only.
- DD-03: el antisolapamiento se valida en la capa de servicios con SQL estándar; no se adopta `EXCLUDE USING gist` como mecanismo principal.
- No hay Docker en la máquina de desarrollo: los tests de C-02 no pueden depender de un PostgreSQL vivo.
- SQLAlchemy es sincrónico; no se introduce async ni una segunda capa de sesión.

## Goals / Non-Goals

**Goals:**

- Un único contrato de esquema, versionado y reversible, que registre las nueve tablas en `Base.metadata`.
- Integridad declarativa donde Postgres la resuelve bien (PK, FK, UNIQUE, CHECK, índices).
- Guardas de aplicación testeables para las dos invariantes que un `CHECK` no cubre: caja inmutable y borrado lógico.
- Seed reproducible, idempotente y testeable sin base real.

**Non-Goals:**

- Endpoints, schemas Pydantic, servicios y routers (siguen en stub).
- Validación de antisolapamiento en servicios y su test de conflicto (C-04, RN-AG-01/R6).
- Login, JWT y RBAC (C-03).
- Migraciones de datos productivos o seed automático al arrancar.
- Limpieza de los módulos huérfanos `lista_espera`, `notificaciones` y `os`.

## Decisions

### D1 — Modelos por módulo, registro central para Alembic y tests

Cada modelo se declara en el `models.py` de su módulo (`admin`: `Usuario`; `agenda`: `Sillon`, `Profesional`, `Turno`, `Bloqueo`; `clinica`: `Paciente`, `Odontograma`, `HallazgoPieza`; `caja`: `MovimientoCaja`). Se agrega `app/db/registry.py`, que importa `Base` y todos los modelos para poblar `Base.metadata`.

- **Por qué**: respeta la organización modular de DD-01 sin crear un `models.py` monolítico, y evita que `migrations/env.py` o los tests dependan de imports accidentales.
- **Alternativa descartada**: un único `app/db/models.py` con las nueve clases. Es más simple, pero concentra dominios que después evolucionan por separado y rompe el paralelismo entre módulo y change dueño.

### D2 — Nombres de tabla en español y plural

`usuarios`, `sillones`, `profesionales`, `pacientes`, `turnos`, `bloqueos`, `odontogramas`, `hallazgos_pieza`, `movimientos_caja`.

- **Por qué**: el dominio, la KB y las reglas están en español; un mapeo mental menos en cada consulta.
- **Alternativa descartada**: inglés (`users`, `appointments`). Coherencia con el resto del proyecto y la cátedra pesa más que la convención genérica.

### D3 — UUID como PK generada por Postgres

`Uuid` de SQLAlchemy 2.0 como tipo de columna, con `default=uuid4` en Python y `server_default=text("gen_random_uuid()")` en la migración.

- **Por qué**: los identificadores aparecen en URLs públicas (`token_publico`) y en logs; un entero secuencial filtra volumen y permite enumeración.
- **Alternativa descartada**: `BIGSERIAL`. Más simple, pero obliga a exponer IDs enumerables y complica el seed determinista.

### D4 — Enums como `VARCHAR` + `CHECK`, no enums nativos

Se usa `Enum(..., native_enum=False, validate_strings=True, create_constraint=True)` con un `CHECK` nombrado por tabla.

- **Por qué**: agregar un valor a un enum nativo requiere `ALTER TYPE`, que Alembic maneja mal y bloquea transacciones. Un `CHECK` se reemplaza con una migración normal.
- **Alternativa descartada**: `ENUM` nativo de Postgres. Mejor tipado, peor costo de evolución para un MVP académico.
- **Riesgo controlado**: el catálogo vive en una tupla Python por dominio, reutilizada por el modelo y por el test que verifica que el `CHECK` de la migración coincide.

### D5 — Timestamps uniformes `timestamptz`

`created_at` y `updated_at` con `server_default=func.now()` y `onupdate=func.now()` en todas las tablas mutables. `MovimientoCaja` solo tiene `fecha` (momento del movimiento) y `created_at`.

- **Por qué**: auditoría homogénea y sin zonas horarias ambiguas en un país con una sola zona.
- **Alternativa descartada**: `timestamp` sin zona. Rompe comparaciones con `now()` y con datos importados.

### D6 — Borrado lógico solo en las cuatro entidades de negocio

`deleted_at: timestamptz | null` en `pacientes`, `turnos`, `profesionales` y `sillones`, con índice parcial o compuesto donde la consulta activa lo justifique. Una guarda `before_delete` de SQLAlchemy lanza excepción para esas clases y evita el `DELETE` físico desde el ORM.

- **Por qué**: cumple R13 sin inventar soft delete donde la KB no lo pide. La guarda convierte la regla en algo testeable ya en C-02.
- **Alternativa descartada**: un `Mixin` aplicado a todas las tablas. `Usuario`, `Odontograma`, `HallazgoPieza` y `MovimientoCaja` tienen reglas propias y no deben heredar semántica de borrado.
- **Límite conocido**: `session.execute(delete(...))` o SQL crudo pueden saltarse la guarda del ORM. Se documenta; si se necesita defensa en profundidad, se evalúa un trigger en un change posterior.

### D7 — Caja inmutable a nivel ORM, no con trigger

`MovimientoCaja` no expone `update`/`delete` en su repositorio y registra listeners `before_update` y `before_delete` que lanzan `ImmutableLedgerError`. La corrección se modela como un movimiento nuevo con `tipo` opuesto, `concepto` aclaratorio y `turno_id` opcional.

- **Por qué**: es testeable sin base y mantiene la migración simple. Un trigger habría que versionarlo, testearlo contra Postgres y explicarlo en la cátedra.
- **Alternativa descartada**: trigger `BEFORE UPDATE OR DELETE`. Más fuerte, pero agrega superficie PL/pgSQL y no corre en los tests estáticos de esta máquina.
- **Riesgo**: SQL crudo puede saltarse la guarda. Ver D6, mismo límite y misma mitigación futura.

### D8 — Antisolapamiento: índices ahora, validación en C-04

C-02 declara los índices `(sillon_id, inicio, fin)` y `(profesional_id, inicio, fin)` y **no** crea un constraint `EXCLUDE`. La validación y el 409 quedan en C-04, según DD-03 y R6.

- **Por qué**: DD-03 decide explícitamente no atarse a `EXCLUDE USING gist`; el baseline ya dejó `btree_gist` disponible por si más adelante se quiere defensa en profundidad.
- **Alternativa descartada**: `EXCLUDE USING gist (sillon_id WITH =, tstzrange(inicio, fin) WITH &&)`. Resuelve la carrera a nivel base, pero contradice DD-03 y complica el test de conflicto pedido en C-04.
- **Deuda registrada**: el comentario de `0001_baseline_btree_gist.py` dice “C-05”; se corrige a C-04 en la medida en que C-02 toque ese archivo solo como comentario, sin cambiar la migración.

### D9 — Seed como plan puro + aplicación idempotente

`app/db/seed.py` expone:

- `build_seed_plan() -> SeedPlan`: datos deterministas (3 sillones, 4 usuarios, 2 profesionales, 2 pacientes) y credenciales de demo.
- `apply_seed(session) -> SeedReport`: resuelve cada entidad por su clave natural (`email`, `matricula`, `dni`, `nombre` del sillón), crea solo lo faltante y devuelve conteos.
- `python -m app.db.seed`: abre sesión, aplica y reporta.

La idempotencia se testea con un repositorio/sesión falsa, sin Postgres.

- **Por qué**: separa el dato del acceso y permite testear la lógica de “crear solo lo que falta” en milisegundos.
- **Alternativa descartada**: `INSERT ... ON CONFLICT DO NOTHING`. Correcto, pero acopla el test a Postgres y no explica qué se creó.
- **Contraseñas**: hashes bcrypt reales para `admin123`, `recepcion123` y `odontologo123` (override por `SEED_DEFAULT_PASSWORD`). Se agrega `bcrypt>=4.1` a las dependencias; C-03 la reutiliza para verificar el login. No se imprimen credenciales en logs.

### D10 — Estrategia de tests sin Postgres vivo

1. **Metadata** (`test_models_structure.py`): importa `app.db.registry`, verifica tablas, PKs UUID, nullability, FKs, únicos, `CHECK` y ausencia de `tenant_id`.
2. **Migración** (`test_migration_0002.py`): inspección estática del archivo — `down_revision == "0001_baseline"`, que las tablas de `Base.metadata` coincidan con las creadas y que los constraints nombrados estén presentes.
3. **Seed** (`test_seed.py`): plan determinista, aplicación idempotente con sesión falsa, conteos y claves naturales.
4. **Integración opcional**: un test marcado `skipif` sin `DATABASE_URL` real; si hay DSN, corre `upgrade head` + seed + downgrade.

- **Por qué**: la máquina no tiene Docker ni Postgres. Los tres primeros niveles cubren el contrato y corren siempre.
- **Alternativa descartada**: `create_all` sobre SQLite. Los `server_default` de Postgres y los `CHECK` con funciones rompen el DDL; un verde falso sería peor que no tenerlo.

### D11 — Drift de nombres y módulos huérfanos

Se actualizan los docstrings de los stubs de `models.py` de `dueño: C-02 core-models-tenancy` a `C-02 core-models-seed`. Los módulos `lista_espera`, `notificaciones` y `os` **no se tocan**: no pertenecen al roadmap de 8 changes y su destino es una decisión separada.

## Risks / Trade-offs

- [Sin Postgres real en la máquina] → La migración se valida de forma estática y en CI; el riesgo se anota como pendiente al archivar, igual que en C-01.
- [Guarda append-only evitable con SQL crudo] → Se documenta el límite; la capa de servicios de C-08 usará el repositorio, y un trigger queda como mejora futura.
- [Enums `VARCHAR` + `CHECK` se desincronizan del catálogo Python] → Una única tupla por dominio alimenta modelo y test; el test compara el `CHECK` de la migración.
- [`bcrypt` entra en C-02 aunque C-03 es dueño del login] → Se justifica por el seed; C-03 no duplica la dependencia. Si se prefiere, el seed puede usar hashes precalculados y mover `bcrypt` a C-03 (ver revisión).
- [Seed ejecutable contra producción por error] → El comando exige `APP_ENV != "production"` salvo `--force`, y no se engancha al arranque.

## Migration Plan

1. `alembic upgrade head` desde `0001_baseline` → crea las nueve tablas, constraints e índices.
2. `python -m app.db.seed` → carga los datos de demostración (idempotente).
3. Rollback: `alembic downgrade 0001_baseline` elimina las tablas de dominio y conserva `btree_gist`.
4. Sin pasos de despliegue: no hay datos productivos ni endpoints que dependan del esquema todavía.

## Open Questions

- ¿Se adopta un trigger de inmutabilidad de caja en C-08 o alcanza con la guarda ORM + repositorio? (No cambia el contrato de C-02.)
- ¿Se agrega `deleted_at` a `Usuario` cuando exista baja de personal? (Hoy R13 no lo exige.)
- ¿Se eliminan los stubs `lista_espera`, `notificaciones` y `os` o se reasignan a un change futuro? (Decisión de roadmap, no de esquema.)

## Decisiones para revisión humana

| # | Decisión | Alternativa | Impacto si se cambia |
|---|----------|-------------|----------------------|
| 1 | Nombres de tabla en español plural | Inglés plural | Renombrar tablas, constraints e índices en la migración |
| 2 | `bcrypt>=4.1` entra en C-02 para hashes del seed | Hashes precalculados; mover `bcrypt` a C-03 | Cambia `pyproject.toml` y el seed |
| 3 | Antisolapamiento solo con índices; sin `EXCLUDE` | `EXCLUDE USING gist` en C-02 | Cambia la migración y adelanta parte de C-04 |
| 4 | Inmutabilidad de caja en ORM | Trigger Postgres | Cambia migración y tests |
| 5 | Seed con `APP_ENV != production` por defecto | Sin guarda de entorno | Riesgo operativo si se corre por error |
