# Auditoría de cobertura de reglas — c-12b-caja-estado-varchar

**Fecha:** 2026-11-13
**Scope:** change `c-12b-caja-estado-varchar` (single change)
**Fuentes leídas:** `knowledge-base/05_reglas_de_negocio.md` (§ RN-CJ), `AGENTS.md` (§ Reglas Duras), `openspec/changes/c-12b-caja-estado-varchar/{proposal,design,tasks,specs/core-data-model/spec}.md`, `backend/src/app/modules/caja/{models,service}.py`, `backend/src/app/db/migrations/versions/{0008_caja_cierre_cuenta_corriente,0015_cierres_estado_varchar}.py`, `backend/test/{test_migration_0015,test_caja_cierre_service,test_caja_cierre_router,test_caja_service,test_caja_router}.py`.

## 1. Catálogo de reglas auditadas

| ID | Texto (resumido) | Fuente | Tipo |
|----|------------------|--------|------|
| RN-CJ-01 | Todo ingreso/egreso registra fecha, monto > 0, medio de pago, concepto y usuario responsable | KB 05 § RN-CJ-01 | negocio |
| RN-CJ-02 | Prohibido el DELETE físico de movimientos; correcciones por contra-asiento | KB 05 § RN-CJ-02 | negocio |
| R2 | NUNCA `tenant_id` (mono-consultorio multi-sillón) | AGENTS.md § Reglas Duras | dura |
| R3 | NUNCA UPDATE/DELETE físico en caja; trazabilidad con movimientos compensatorios | AGENTS.md § Reglas Duras | dura |
| R5 | Type hints + `snake_case`; todo cambio de schema con migración Alembic | AGENTS.md § Reglas Duras | dura |
| R7 | NUNCA `any` en TS; componentes `PascalCase` | AGENTS.md § Reglas Duras | dura |
| R13 | NUNCA borrado físico en tablas de negocio; borrado lógico con `deleted_at` | AGENTS.md § Reglas Duras | dura |

Reglas del catálogo global fuera de alcance (➖ N/A, ver §2): RN-AG-*, RN-CL-01, RN-SEG-01, RN-G-01, R1, R4, R6, R8–R12; el change no toca agenda, clínica, logs, notificaciones, schemas Pydantic, RBAC, UI ni commits.

## 2. Matriz de cobertura

| Regla | Artefacto que la cubre | Estado | Verificación |
|-------|------------------------|--------|--------------|
| RN-CJ-01 | Pre-existente: `test_caja_service.py::test_registrar_ingreso_asocia_usuario`, `test_caja_router.py::test_body_con_usuario_422`, `test_caja_router.py::test_monto_cero_422` | ✅ | La migración `0015` no altera columnas del libro ni la firma del servicio; los tres tests pasan en la suite completa final |
| RN-CJ-02 | Pre-existente: `test_caja_service.py::test_contra_asiento_son_dos_filas`, `test_caja_cierre_router.py::test_no_patch_delete_movimientos`; triggers `trg_ajustes_no_modificar` / `trg_cierres_no_modificar` (0008) intactos | ✅ | El change no toca triggers ni el libro; los tests de inmutabilidad pasan; la migración solo hace DDL de tipo sobre `cierres_caja.estado` |
| R2 | `spec.md` scenario "Sin multi-tenant"; `test_migration_0015.py::test_sin_tenant_id` | ✅ | Aserción estática: `"tenant_id" not in` el texto de la migración |
| R3 | `design.md` § Non-Goals; verificación empírica (3 filas con los 3 estados conservadas tras upgrade y downgrade) | ✅ | Ningún `UPDATE`/`DELETE`/`DROP TABLE` en `0015`; datos preservados en el round-trip |
| R5 | `0015_cierres_estado_varchar.py` (anotaciones `revision: str`, `down_revision: str \| None`, `upgrade() -> None`), `test_migration_0015.py`, `test_migration_revision_ids.py` | ✅ | `revision` de 27 chars (≤ 32); un único head; 13 tests verdes |
| R7 | — | ➖ N/A | Change backend-only: no hay archivos `.ts`/`.tsx` ni componentes React modificados |
| R13 | `0015` no dropea tablas ni columnas; `DROP TYPE IF EXISTS estado_cierre` solo borra el tipo del catálogo | ✅ | Round-trip `upgrade → downgrade → upgrade` sin pérdida de filas ni objetos huérfanos |

### Escenarios del spec nuevo

| Escenario | Artefacto | Estado | Verificación |
|-----------|-----------|--------|--------------|
| Upgrade convierte el tipo | `test_migration_0015.py` (tipo/CHEC/default/USING) + verificación empírica manual | ⚠️ parcial | El test es estático (texto); la verificación real del catálogo (`information_schema`, `pg_type`) se hizo a mano, no hay test de integración automatizado de esquema |
| Datos existentes preservados | Verificación empírica manual (3 filas `pendiente`/`cerrado`/`reabierto`) | ⚠️ parcial | Sin test automatizado de preservación de datos |
| Downgrade restaura el ENUM | `test_migration_0015.py` (CREATE TYPE, `USING`, `drop_constraint`) + round-trip manual | ⚠️ parcial | El round-trip se ejecutó a mano sobre `odonto_test`; no está automatizado |
| Sin multi-tenant | `test_migration_0015.py::test_sin_tenant_id` | ✅ | Aserción estática |

## 3. Ambigüedades detectadas

- **Nombre del CHECK**: el spec y las tasks dicen "el CHECK `estado`", pero la `naming_convention` del proyecto (`ck_%(table_name)s_%(constraint_name)s`, `backend/src/app/db/base.py`) materializa el constraint como `ck_cierres_caja_estado`. **Lectura A:** el nombre físico debe ser literalmente `estado`. **Lectura B:** `estado` es el nombre lógico y la convención agrega el prefijo (consistente con el `CheckConstraint(name="estado")` del modelo). **Propuesta:** adoptar B y aclararlo en el spec (`CHECK lógico \`estado\` → físico \`ck_cierres_caja_estado\``). No requiere cambio de código: el modelo y la migración ya coinciden.
- **Número de migración en `proposal.md`**: el proposal cita `0008_caja_cierre_cta_cte` en "Why" y `spec.md` también, mientras `design.md` cita `0008_caja_cierre_cuenta_corriente` (nombre del archivo). La revisión real es `0008_caja_cierre_cta_cte`. **Propuesta:** unificar la cita en `design.md` (corrección documental, sin impacto funcional).

## 4. Conflictos detectados

- Ninguno entre reglas duras y artefactos del change. R2, R3, R5 y R13 se cumplen; donde el texto del spec difiere del nombre físico del constraint, prevalecen el modelo y la `naming_convention` del proyecto (ver §3, ambigüedad 1).

## 5. Cobertura faltante propuesta

### 5.1 Escenarios (Given/When/Then)

> **Given** una base migrada a `0014_pagos_simulados` con al menos un cierre en cada estado del catálogo
> **When** se ejecuta `alembic upgrade head`
> **Then** `information_schema.columns` reporta `character varying(20)` y `column_default = 'pendiente'::character varying`, `pg_type` no contiene `estado_cierre`, existe `ck_cierres_caja_estado` y las filas conservan el mismo texto de estado

### 5.2 Casos de test

- `backend/test/test_migration_0015_integration.py::test_upgrade_convierte_columna_y_borra_enum` (marker `integration`, contra `odonto_test`): refleja el esquema real y compara tipo/default/CHECK/`pg_type`.
- `...::test_downgrade_restaura_enum_sin_objetos_huerfanos`: hace `downgrade` y verifica `USER-DEFINED` + tipo presente + CHECK ausente.
- `...::test_datos_preservados_en_round_trip`: inserta los 3 estados antes del upgrade y compara tuplas después.

### 5.3 Criterios para tasks.md

- Añadir en un change de calidad posterior (no en C-12b, que declaró fuera de alcance los tests de integración de esquema) la verificación automatizada de los cuatro escenarios del spec.

## 6. Resumen cuantitativo

- Reglas auditadas: 7 (RN-CJ-01, RN-CJ-02, R2, R3, R5, R7, R13)
- ✅ cubiertas: 6 (RN-CJ-01, RN-CJ-02, R2, R3, R5, R13)
- ⚠️ parciales: 0 reglas (3 escenarios del spec quedan en verificación manual)
- ❌ sin cobertura: 0 reglas
- ➖ N/A: 1 (R7)

## 7. Revisión crítica

- **Omisión/error detectado:** las tasks 1.2/1.3 y la verificación empírica exigen comprobar tipo, default, CHECK y `pg_type`, pero el único test automatizado es estático (lee el texto del archivo). Un cambio futuro que rompa la migración en PostgreSQL —por ejemplo, invertir el orden `DROP DEFAULT` / `ALTER TYPE`— seguiría pasando `pytest -m "not integration"` sin detectarse.
- **Cómo se detectó:** al mapear el escenario "Upgrade convierte el tipo" del `spec.md` contra los artefactos reales, no existe ningún test que consulte el catálogo de PostgreSQL.
- **Fuente que permitió corregir:** `design.md` § D4 (acepta la verificación empírica vía suite de caja) + `spec.md` § Escenarios (exige tipo/default/CHECK/`pg_type`).
- **Antes:** `tasks.md` 2.1 solo pide "test de migración" estático; el spec promete cuatro condiciones verificables en la base.
- **Después (propuesta):** agregar en un change de calidad los tests de integración de esquema listados en §5.2; mientras tanto, la verificación empírica de este change queda registrada en `tasks.md` 3.1/3.2.
