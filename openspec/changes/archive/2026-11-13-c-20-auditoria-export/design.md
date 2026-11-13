# Design

## Context

Ver `proposal.md`. El estado relevante:
- No existe ningún módulo de auditoría; las escrituras de turnos, caja, presupuestos y odontograma no dejan rastro.
- El esquema usa `String` + `CHECK` para catálogos (no ENUM nativo) y `JSONB` está disponible en PostgreSQL 15+.
- La cadena de migraciones termina en `0015_cierres_estado_varchar` (C-12b archivado). El siguiente número libre es `0016`.
- `alembic_version.version_num` es `varchar(32)`; el guard `test_migration_revision_ids.py` valida la longitud.
- Gobernanza: **CRÍTICO** (caja/auditoría). La implementación no se ejecuta sin aprobación humana explícita.

## Goals / Non-Goals

**Goals:**
- Tabla `auditorias` + migración `0016` reversible.
- Helper `registrar_auditoria` atómico con la escritura auditada.
- Enmascarado centralizado aplicado al persistir y al exportar.
- Visor paginado y export CSV para `admin`, con filtros solo no sensibles.
- Hooks en turnos, caja, presupuestos y odontograma.

**Non-Goals:**
- No se modifica la lógica de negocio de los módulos hookeados; solo se agrega la llamada al helper.
- No se toca append-only de caja (R3) ni borrado lógico (R13).
- No se agrega firma/hash-chain de inmutabilidad ni retención automática (deuda).
- No se agregan tests de caja no deterministas ni se arregla el stale de agenda (C-22).
- Visor UI mínimo o solo API: se define API-first; UI es opcional en una tarea separada.
- No se integra con sistemas externos.

## Decisions

### D1 — Helper explícito en la capa de servicio (no event listener)
**Decisión:** función `registrar_auditoria(db, *, usuario_id, accion, recurso, recurso_id, diff, ip=None, user_agent=None)` invocada explícitamente dentro de cada servicio, en la misma sesión/transacción.
**Alternativas:**
- *Event listener de SQLAlchemy (`after_insert`/`after_update`)*: captura todo automáticamente, pero no tiene acceso al `usuario_id` del JWT ni al diff semántico; y dispararía en escrituras internas no sensibles. Se descarta.
- *Middleware HTTP*: tendría el usuario, pero no el diff ni el recurso tipado, y no garantiza atomicidad por transacción. Se descarta.
**Rationale:** explícito es testeable, tipado, y fuerza a decidir qué se audita. Mitigación del "olvido": checklist de hooks + test de integración que verifica que cada escritura sensible genera fila.

### D2 — Enmascarado en escritura (y re-aplicado en export)
**Decisión:** el `diff` se enmascara antes de persistir; el export re-aplica la máscara sobre lo leído (defensa en profundidad). Lista de denegación configurable en `masking.py` (motivos clínicos, observaciones, diagnósticos, documentos, notas, etc.).
**Alternativas:**
- *Enmascarar solo en export*: el `diff` en BD queda con PII y cualquier consulta directa filtra. Se descarta (R9).
- *No guardar diff, solo metadatos*: pierde valor de auditoría. Se descarta.
**Rationale:** la BD nunca contiene PII de salud en `auditorias`; cumple R9 incluso ante acceso directo a la base.

### D3 — `accion` y `recurso` como varchar + CHECK (no ENUM nativo)
**Decisión:** catálogos controlados con `CheckConstraint`, consistente con `turnos.estado` y con el fix de C-12b.
**Rationale:** evita el bug `UndefinedFunction` y permite agregar valores con migración.

### D4 — RBAC: solo `admin` consulta y exporta
**Decisión:** endpoints protegidos con dependencia de rol `admin`; `recepcion` y `odontologo` reciben 403.
**Rationale:** la auditoría es de cumplimiento/seguridad; la matriz RBAC de KB 03 asigna la gestión de usuarios/auditoría al admin. (Confirmar con el humano si odontólogo debe ver auditoría de sus propios pacientes; por defecto, no.)

### D5 — Paginación y export por filtros no sensibles
**Decisión:** filtros `fecha_desde`, `fecha_hasta`, `recurso`, `accion`, `usuario_id`, `page`, `size`. Sin búsqueda de texto libre sobre `diff` ni sobre campos clínicos (R9). Export con tope de filas (p. ej. 10 000) y streaming.

### D6 — Atomicidad: misma transacción
**Decisión:** `registrar_auditoria` usa la misma `Session`/transacción que la escritura de negocio; si falla, se propaga la excepción y se revierte todo. No se captura ni se loguea silenciosamente.

### D7 — Migración `0016_auditoria`
**Decisión:** `revision = "0016_auditoria"` (16 chars ≤ 32), `down_revision = "0015_cierres_estado_varchar"`, `upgrade`/`downgrade` simétricos, sin `tenant_id`.

## Risks / Trade-offs
- **Auditoría falla y tumba escrituras de negocio** → mitigación: tests de integración que fuerzan el fallo y verifican rollback; el helper es simple (un INSERT).
- **Volumen**: una fila por escritura sensible; índices en `fecha` y `(recurso, recurso_id)` para consultas paginadas. Retención automática queda fuera de alcance (deuda).
- **PII en `diff`**: mitigado por enmascarado en escritura + export; revisión de la lista de denegación en code review.
- **CSV enorme**: tope de filas + streaming; si se supera el tope, devolver 413 o paginar.
- **Olvido de hook en un endpoint nuevo**: mitigado por checklist + test de integración por módulo; no hay enforcement automático (deuda).
- **`usuario_id` nulo** (jobs/sistema): permitido; se registra `NULL`.

## Deuda conocida (fuera de alcance)
- Hash-chain / firma de inmutabilidad de `auditorias` (append-only criptográfico).
- Retención/purga automática.
- UI completa del visor (solo API en este change).
- Tests de caja no deterministas y stale de agenda (C-22).
- Enforcement automático de hooks (lint/AST).

## Migration Plan
1. Aprobación humana explícita.
2. Implementar `0016_auditoria` y `test_migration_0016.py`.
3. `alembic upgrade head` en `odonto` y `odonto_test`.
4. Implementar módulo `audit`, helper, masking, router.
5. Agregar hooks en turnos, caja, presupuestos, odontograma.
6. Tests unitarios + integración (hooks, RBAC, paginación, export, masking, atomicidad).
7. Rollback: `alembic downgrade 0015_cierres_estado_varchar`.

**Gobernanza: CRÍTICO (auditoría).** La implementación NO se ejecuta sin aprobación humana explícita de `proposal.md`, `design.md` y `tasks.md`. La validación del CLI no sustituye esa aprobación.

## Open Questions
- ¿`odontologo` debe poder ver auditoría de sus propios pacientes? (Por defecto: no, solo `admin`.) Confirmar con el humano.
- ¿El visor requiere UI en este change o se entrega solo API? (Por defecto: API-first; UI mínima opcional.)