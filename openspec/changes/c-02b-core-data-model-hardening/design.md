# Design — C-02b core-data-model-hardening

## Context

Ver `proposal.md` — Why. C-02 quedó archivado con la spec `core-data-model` viva, pero la auditoría de reglas detectó brechas entre esa spec y el código. El esquema ya está aplicado en PostgreSQL 17 (instancia temporal `5433`) y no hay datos productivos: es el momento barato para endurecer el contrato antes de C-03/C-04.

Restricciones: R3 y R13 son reglas duras y no admiten excepciones; el proyecto usa TDD estricto; no se agregan dependencias nuevas.

## Goals / Non-Goals

**Goals:**

- Que la base, y no solo el ORM, garantice email canónico, motivo no vacío, coherencia `fin`/`duracion_min`, caja inmutable y borrado lógico.
- Dejar tests que prueben esas garantías por SQL directo contra PostgreSQL real (cuando haya DSN).
- Aclarar la spec de profesionales y dejar documentados los handoffs a C-04/C-07/C-08.

**Non-Goals:**

- Implementar autenticación (C-03), servicios de agenda (C-04) o caja (C-08).
- Crear un catálogo de prestaciones: es una decisión de dominio abierta.
- Migrar datos productivos: no existen todavía.

## Decisions

### D1 — Email canónico en app y en base

`Usuario` normaliza con `@validates("email")` (`strip().lower()`), y la base agrega `ck_usuarios_email_normalizado` con `email = lower(btrim(email))`. Se conserva el `UNIQUE(email)` existente.

- **Por qué**: el `CHECK` hace imposible persistir un email no canónico aunque se saltee el ORM; el `UNIQUE` case-sensitive alcanza porque todos los valores quedan en minúsculas.
- **Alternativas descartadas**: índice único funcional `lower(email)` (redundante con el `CHECK`); `citext` (extensión extra y menos explícita).

### D2 — Motivo de bloqueo con contenido real

`ck_bloqueos_motivo_no_vacio`: `length(btrim(motivo)) > 0`.

- **Por qué**: `NOT NULL` acepta `"   "`; la spec pide “motivo no vacío”.
- **Alternativa descartada**: validación solo en servicio (no protege inserciones directas).

### D3 — Coherencia `fin`/`duracion_min` en base

`ck_turnos_fin_coherente`: `fin = inicio + (duracion_min * interval '1 minute')`.

- **Por qué**: RN-AG-02 dice que `fin` se calcula desde `inicio + duracion`; hoy hay dos columnas que pueden contradecirse.
- **Contrapartida**: C-04 debe calcular `fin` con esa misma fórmula. Si en el futuro se permiten duraciones con segundos, la constraint se revisa.
- **Alternativa descartada**: validar solo en el servicio de C-04 (deja la puerta abierta a inserciones directas inconsistentes).

### D4 — Triggers de base como defensa en profundidad

Se agregan funciones y triggers:

- `fn_forbid_ledger_mutation()` + `trg_movimientos_caja_inmutable` (`BEFORE UPDATE OR DELETE`) y `trg_movimientos_caja_no_truncate` (`BEFORE TRUNCATE`).
- `fn_forbid_physical_delete()` + triggers `BEFORE DELETE` y `BEFORE TRUNCATE` en `pacientes`, `turnos`, `profesionales` y `sillones`.

Las guardas ORM de `app/db/base.py` se mantienen para dar errores tempranos y legibles; los triggers cubren SQL crudo y `TRUNCATE`.

- **Por qué**: R3 y R13 dicen “NUNCA”; una guarda solo-ORM es evitable con `DELETE` directo.
- **Alternativas descartadas**: solo ORM con riesgo documentado (no cumple la regla dura); RLS (no aplica a inmutabilidad); event triggers de DDL (demasiado amplios).
- **Límite conocido**: `DROP TABLE`/DDL sigue siendo posible para el rol dueño; eso es administración de esquema, no operación de negocio.

### D5 — Nombre de profesional no único

Se corrige la redacción de la spec: `nombre` obligatorio, `matricula` única, `usuario_id` único cuando no es nulo. No se agrega unique sobre `nombre`.

- **Por qué**: dos odontólogos pueden llamarse igual; la KB 04 solo pide matrícula.
- **Alternativa descartada**: unique de `nombre` (rechazaría homónimos legítimos).

### D6 — Seed con error operativo claro

`main()` envuelve la creación de sesión y la aplicación del seed en `try/except SQLAlchemyError`: hace rollback, imprime un mensaje accionable por `stderr` (“verificá DATABASE_URL y alembic upgrade head”) y devuelve `1`. Los errores no relacionados con base siguen propagándose.

- **Por qué**: la spec exige “mensaje operativo claro y sin datos parciales”; hoy sale un traceback crudo.
- **Alternativa descartada**: capturar `Exception` genérica (ocultaría bugs de lógica).

### D7 — Tests por capas

1. **Unitarios**: validador de email, constraints en `Base.metadata`, seed con sesión falsa.
2. **Estáticos de migración**: `0003` declara constraints, funciones, triggers y downgrade.
3. **Integración opcional**: `test_pg_hardening.py`, con `skipif` si no hay `DATABASE_URL`; prueba SQL directo (email con mayúsculas, motivo vacío, `fin` incoherente, `UPDATE`/`DELETE`/`TRUNCATE`).
4. **Seed sin base**: monkeypatch de `get_session_factory` que lanza `OperationalError`; se verifica rollback, mensaje y código de salida.

- **Por qué**: la máquina no siempre tiene PostgreSQL; los tres primeros niveles corren siempre y el cuarto se ejecuta cuando hay DSN.

### D8 — Handoff documental

- `CHANGES.md`: agregar a C-04/C-07/C-08 el criterio “toda consulta activa filtra `deleted_at IS NULL`”.
- `knowledge-base/10_preguntas_abiertas.md`: registrar (a) duración por prestación sin catálogo `Prestacion`, (b) momento de deducción de la seña (RN-CJ-03), (c) aceptación de triggers en producción.

## Risks / Trade-offs

- [La migración falla si hay filas inconsistentes] → pre-check SQL antes de aplicar; el seed actual no genera turnos, bloqueos ni emails con mayúsculas.
- [Triggers bloquean limpiezas manuales] → es el comportamiento buscado; para entornos de prueba se recrea la base, no se borran filas.
- [Doble validación ORM + trigger] → el ORM da el error amigable primero; el trigger es la red de seguridad.
- [`TRUNCATE` no dispara triggers de fila] → se agregan triggers `BEFORE TRUNCATE` explícitos.
- [`fin` con segundos] → la constraint asume granularidad de minutos; si cambia, se versiona una migración nueva.

## Migration Plan

1. Pre-check en PostgreSQL: emails no canónicos, bloqueos con motivo vacío, turnos con `fin` incoherente.
2. `alembic upgrade head` → aplica `0003_core_data_model_hardening`.
3. `python -m app.db.seed` → sigue siendo idempotente.
4. Rollback: `alembic downgrade 0002_core_models` → elimina constraints, triggers y funciones; conserva tablas y datos.
5. Verificación real en la instancia temporal de PostgreSQL 17.

## Open Questions

- ¿Se agrega un catálogo `Prestacion` para derivar duración, o queda manual/por profesional?
- ¿En qué estado del turno se considera devengada o retenida la seña? (C-08)
- ¿Se aceptan los triggers como parte del esquema académico o se documentan como opcionales? (recomendado: sí)

## Decisiones para revisión humana

| # | Decisión | Alternativa | Impacto si se cambia |
|---|----------|-------------|----------------------|
| 1 | Triggers de base para R3/R13 | Solo guardas ORM | Se cae la defensa ante SQL directo |
| 2 | `CHECK` de coherencia `fin` | Validación solo en C-04 | Queda posible un turno inconsistente por inserción directa |
| 3 | `CHECK` de email canónico + unique existente | Índice único funcional `lower(email)` | Cambia la migración `0003` |
| 4 | Triggers `BEFORE TRUNCATE` | Solo triggers de fila | `TRUNCATE` podría vaciar tablas de negocio |
| 5 | Actualizar `CHANGES.md` y `KB 10` en este change | Dejarlo para C-03 | Se pierde el handoff documental |
