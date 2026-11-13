# Design

## Context

Ver `proposal.md` — Why. El estado actual relevante:

- `backend/src/app/db/migrations/versions/0008_caja_cierre_cuenta_corriente.py` crea `cierres_caja.estado` con `sa.Enum("pendiente", "cerrado", "reabierto", name="estado_cierre")`.
- `backend/src/app/modules/caja/models.py` declara `estado: Mapped[str] = mapped_column(String(20), nullable=False)` y un `CheckConstraint("estado IN ('pendiente', 'cerrado', 'reabierto')", name="estado")`.
- `backend/src/app/modules/caja/service.py` filtra con `CierreCaja.estado == "cerrado"` (bloqueo de período, cierre y cuenta corriente).
- El resto del esquema usa `String` + `CHECK` para catálogos (`turnos.estado`, `hallazgos_pieza.estado`, `usuarios.rol` en `0002_core_models.py`). `cierres_caja.estado` es la única columna con ENUM nativo.
- La suite de integración contra PostgreSQL real (`odonto_test`) falla con `psycopg.errors.UndefinedFunction` en todos los caminos que filtran por estado.
- Restricciones: `alembic_version.version_num` es `varchar(32)` y existe el guard `backend/test/test_migration_revision_ids.py`; la cadena termina hoy en `0014_pagos_simulados`.

## Goals / Non-Goals

**Goals:**

- Que `cierres_caja.estado` sea `varchar(20)` + `CHECK` también en PostgreSQL, igual que en el modelo y en el resto del esquema.
- Que los endpoints de cierre, cuenta corriente y ajustes dejen de responder 500 contra PostgreSQL real.
- Dejar una migración `0015` reversible, con `upgrade`/`downgrade` simétricos y sin objetos huérfanos.
- Cubrir la migración con un test estático/estructural en el estilo de `test_migration_0004.py` … `test_migration_0006.py`.

**Non-Goals:**

- No se modifica el modelo, el servicio, los schemas ni los routers: ya son correctos; el defecto es solo de la base.
- No se tocan migraciones históricas (`0008` queda como está; su corrección vive en `0015`).
- No se toca la lógica append-only, los triggers de inmutabilidad ni datos del libro.
- No se corrigen los tests de caja no deterministas ni el test desactualizado de agenda (deuda de calidad, ver más abajo).

## Decisions

### D1 — Convertir a `varchar(20)` + CHECK en lugar de mantener el ENUM

**Decisión:** alinear la base con el modelo y con la convención del esquema usando `varchar(20)` y un `CHECK` nombrado `estado`.

**Alternativas consideradas:**

- *Cambiar el modelo a `sa.Enum`*: obligaría a tocar modelo, schemas y servicio, y dejaría a `cierres_caja` como excepción frente a `turnos`, `hallazgos_pieza` y `usuarios`. Se descarta por inconsistencia y mayor superficie de cambio.
- *Dejar el ENUM y castear en cada query*: parchea el síntoma, no la causa, y mantiene la divergencia. Se descarta.

**SQL de referencia validado empíricamente:**

```sql
ALTER TABLE cierres_caja ALTER COLUMN estado DROP DEFAULT;
ALTER TABLE cierres_caja ALTER COLUMN estado TYPE varchar(20) USING estado::text;
ALTER TABLE cierres_caja ALTER COLUMN estado SET DEFAULT 'pendiente';
DROP TYPE IF EXISTS estado_cierre;
ALTER TABLE cierres_caja ADD CONSTRAINT estado CHECK (estado IN ('pendiente', 'cerrado', 'reabierto'));
```

En Alembic se implementa con `op.alter_column(..., type_=sa.String(20), postgresql_using="estado::text", server_default=...)`, `op.create_check_constraint` / `op.drop_constraint` y `op.execute("DROP TYPE IF EXISTS estado_cierre")`. El chequeo `DROP DEFAULT` previo evita que el cast arrastre el default del ENUM; el default se restablece como texto `'pendiente'`.

### D2 — Migración `0015_cierres_estado_varchar`, encadenada a `0014_pagos_simulados`

**Decisión:** archivo `backend/src/app/db/migrations/versions/0015_cierres_estado_varchar.py`, con `revision = "0015_cierres_estado_varchar"` (27 caracteres, dentro del límite de 32) y `down_revision = "0014_pagos_simulados"`.

**Rationale:** es la única forma de que `alembic upgrade head` llegue a la base de integración sin romper el guard de longitud y sin reescribir historia. `0015` es el siguiente número libre (`0014` está tomada por C-17); el cambio es incremental y auditable.

### D3 — `downgrade` simétrico y reversible

**Decisión:** el `downgrade` hace, en orden inverso: elimina el `CHECK` `estado`, quita el default, recrea el tipo `estado_cierre`, castea la columna al ENUM con `postgresql_using="estado::estado_cierre"` y restablece el default `'pendiente'`.

**Rationale:** el spec vigente exige reversibilidad. El orden importa: no se puede castear a un tipo inexistente ni borrar un tipo en uso. Los valores del catálogo son idénticos, así que el cast de vuelta no pierde datos.

### D4 — Verificación con test de migración estructural

**Decisión:** nuevo `backend/test/test_migration_0015.py` que verifica, sin depender de PostgreSQL: que el archivo existe, `revision`/`down_revision`, el `alter_column` a `String(20)` con `postgresql_using`, el `DROP TYPE IF EXISTS estado_cierre`, el `create_check_constraint`/`drop_constraint` y el `server_default='pendiente'` en ambos sentidos.

**Rationale:** sigue el patrón de `test_migration_0004.py`, `0005` y `0006` (checks estáticos sobre el texto), corre en la suite rápida y protege la reversibilidad. La verificación empírica del tipo real en `pg_type`, del CHECK y del `server_default` se hace con la suite de integración de caja contra `odonto_test`, que es el RED que este change debe poner en verde.

## Risks / Trade-offs

- **Bloqueo breve de la tabla durante el `ALTER COLUMN TYPE`** → la tabla `cierres_caja` es pequeña (una fila por día); el cast se hace en una sola transacción de migración. Aceptable para un consultorio mono-sede.
- **Valores fuera del catálogo en bases existentes** → el `CHECK` fallaría al crearse. Mitigación: los únicos valores posibles hoy son los del ENUM original (`pendiente`, `cerrado`, `reabierto`), por lo que el cast no introduce valores nuevos.
- **El `downgrade` puede fallar si en el futuro se agregan estados nuevos** → mitigación: el `downgrade` castea explícitamente; cualquier estado nuevo exigirá una migración propia y su downgrade correspondiente. Se documenta como límite conocido.
- **El `DROP TYPE IF EXISTS` es destructivo si otra tabla usara el tipo** → verificado: `estado_cierre` solo lo usa `cierres_caja.estado`. Se deja el `IF EXISTS` para idempotencia.
- **`revision` demasiado largo rompe `alembic upgrade` en PostgreSQL** (bug real de `0008`) → mitigación: `0015_cierres_estado_varchar` tiene 27 caracteres y el guard `test_migration_revision_ids.py` lo valida.

## Deuda conocida (fuera de alcance)

La suite completa contra `odonto_test` parte de 20 fallos. Esta conversión los reduce a 10; los 10 restantes son deuda de tests y van a un change de calidad posterior:

- 9 tests de caja no deterministas: fixtures con turnos en horarios fijos que chocan con el antisolapamiento (C-09a), saldos que se contaminan entre tests e IDs inexistentes.
- `backend/test/test_agenda_rango_router.py::test_turno_out_conserva_todos_los_campos`, desactualizado: no incluye el campo `origen` que agregó C-10.

Este change no los toca: su criterio de aceptación es que los tests de integración de cierre/cuenta corriente/ajustes que hoy fallan por el ENUM pasen, no que la suite completa quede en verde.

## Migration Plan

1. Aprobación humana explícita (ver gobernanza abajo).
2. Implementar `0015_cierres_estado_varchar` y el test `0015`.
3. `cd backend; alembic upgrade head` sobre la base local (`odonto`).
4. Sembrar si hace falta (`python -m app.db.seed`, idempotente).
5. Aplicar la migración a `odonto_test` y correr la suite de integración de caja.
6. Rollback: `alembic downgrade 0014_pagos_simulados` (recrea el ENUM y vuelve el tipo).

**Gobernanza: CRÍTICO (caja).** Este change toca el esquema contable. La implementación NO se ejecuta sin aprobación humana explícita del `proposal.md`, del `design.md` y de la lista de `tasks.md`. La validación `openspec validate --strict` no sustituye esa aprobación.

## Open Questions

- (ninguna) Las decisiones de tipo, encadenamiento, reversibilidad y alcance de tests están cerradas.
