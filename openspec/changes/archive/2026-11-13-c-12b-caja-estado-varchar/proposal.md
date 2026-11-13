# Proposal

## Why

La migración `0008_caja_cierre_cta_cte` creó `cierres_caja.estado` como ENUM nativo de PostgreSQL (`estado_cierre`), pero el modelo SQLAlchemy y el resto del esquema lo tratan como `String(20)` + `CHECK`. Contra PostgreSQL real, cualquier consulta que filtre por estado —`CierreCaja.estado == "cerrado"` en el servicio de caja— falla con `UndefinedFunction: el operador no existe: estado_cierre = character varying`, y los endpoints de cierre, cuenta corriente y ajustes devuelven 500. En SQLite no se detectó porque los tests de caja son `integration` y el gate rápido nunca los ejecutó. Corregir ahora desbloquea media suite de integración y elimina la única divergencia de tipos del esquema.

## What Changes

- **BREAKING (schema)**: convertir `cierres_caja.estado` de ENUM nativo `estado_cierre` a `varchar(20)` con `CHECK (estado IN ('pendiente', 'cerrado', 'reabierto'))`, alineado con `turnos.estado`, `hallazgos_pieza.estado` y `usuarios.rol`.
- Nueva migración reversible `0015_cierres_estado_varchar` (`down_revision = "0014_pagos_simulados"`): `upgrade` castea la columna y elimina el tipo ENUM; `downgrade` recrea el ENUM y vuelve la columna a ese tipo.
- Test de migración nuevo que verifica tipo `varchar(20)`, ausencia de `estado_cierre` en `pg_type`, existencia del CHECK `estado` y `server_default = 'pendiente'`.
- Se hacen pasar los tests de integración de caja que hoy fallan con 500; no se toca el modelo ni el servicio, que ya son correctos.

## Capabilities

### New Capabilities

- (ninguna)

### Modified Capabilities

- `core-data-model`: el tipo de `cierres_caja.estado` pasa de ENUM nativo a `varchar(20)` + CHECK, y se agrega el requisito de la migración reversible `0015`.

## Impact

- **Backend / base de datos**: `cierres_caja.estado` cambia de tipo en PostgreSQL; el tipo `estado_cierre` se elimina. Requiere `alembic upgrade head`.
- **Código**: solo migración nueva + test de migración. Sin cambios en modelos, schemas, servicios ni routers.
- **Tests**: se desbloquean los tests de integración de cierre/cuenta corriente/ajustes (10 fallos de la suite completa, ver deuda fuera de alcance en `design.md`).
- **Dependencias**: C-12 (caja-cierre) y C-17 (migración `0014`, padre de la cadena). Sin nuevas dependencias externas.
- **Reglas duras**: R2 (sin `tenant_id`), R5 (migración Alembic + type hints/snake_case), R3/R13 (no se tocan triggers ni datos del libro).
