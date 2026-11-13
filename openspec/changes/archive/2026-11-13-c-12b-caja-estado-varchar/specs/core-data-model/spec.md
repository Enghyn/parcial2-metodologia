# Spec Delta

## MODIFIED Requirements

### Requirement: Tablas de cierre, cuenta corriente y ajustes

El sistema SHALL crear mediante la migración `0008_caja_cierre_cta_cte` (encadenada a `0007_ficha_clinica_avanzada` y reversible con `downgrade`) las tablas `cierres_caja`, `cuentas_corrientes_paciente` y `ajustes_caja`, con sus índices, claves foráneas y check constraints, sin `tenant_id` (R2).

#### Sub-requirement: cierres_caja

`cierres_caja` SHALL tener: `id` (UUID PK), `fecha_dia` (Date, UNIQUE), `estado` (varchar(20) con CHECK: `pendiente`, `cerrado`, `reabierto`), `balance` (Numeric 10,2), `total_ingresos` (Numeric 10,2), `total_egresos` (Numeric 10,2), `aprobado_por` (FK opcional a `usuarios`), `aprobado_en` (timestamp nullable), `created_at`. Solo `admin` puede pasar un cierre a `cerrado`.

#### Scenario: Cierre con estado cerrado y aprobador

- **WHEN** se aplica la migración y se crea un cierre aprobado por admin
- **THEN** `cierres_caja` tiene `estado = cerrado`, `aprobado_por` no nulo y `aprobado_en` con fecha

#### Scenario: Estado fuera del catálogo

- **WHEN** se intenta persistir un cierre con `estado` distinto de `pendiente`, `cerrado` o `reabierto`
- **THEN** la base rechaza la operación por violación del CHECK `estado`

#### Sub-requirement: cuentas_corrientes_paciente (saldo derivado)

`cuentas_corrientes_paciente` SHALL ser una tabla derivada/materializada con `paciente_id` (FK a `pacientes`, UNIQUE), `saldo` (Numeric 10,2 derivado de movimientos vinculados a turnos del paciente) y `actualizado_en`. El saldo SHALL recalcularse desde `movimientos_caja` (no es fuente de verdad autónoma).

#### Scenario: Saldo cero para paciente sin movimientos

- **WHEN** un paciente no tiene movimientos vinculados
- **THEN** su saldo en `cuentas_corrientes_paciente` es cero

#### Sub-requirement: ajustes_caja

`ajustes_caja` SHALL tener: `id` (UUID PK), `movimiento_corregido_id` (FK a `movimientos_caja`), `movimiento_ajuste_id` (FK a `movimientos_caja`, el contra-asiento), `motivo` (String, no vacío), `fecha` (timestamp), `usuario_aprobador_id` (FK a `usuarios`, solo `admin`). SHALL bloquear UPDATE/DELETE por trigger (append-only).

#### Scenario: Ajuste vinculado a contra-asiento

- **WHEN** se registra un ajuste con motivo y contra-asiento
- **THEN** `ajustes_caja` vincula el movimiento original con el contra-asiento y registra al aprobador

## ADDED Requirements

### Requirement: Migración 0015 reversible de estado de cierre

La migración `0015_cierres_estado_varchar` SHALL convertir `cierres_caja.estado` de ENUM nativo a `varchar(20)` con `CHECK` y `server_default = 'pendiente'`, eliminar el tipo `estado_cierre` del catálogo `pg_type` y revertir el cambio en `downgrade`, encadenada a `0014_pagos_simulados` y con `revision` de 32 caracteres o menos.

#### Scenario: Upgrade convierte el tipo

- **WHEN** se ejecuta `alembic upgrade head` sobre una base con `0014_pagos_simulados` aplicada
- **THEN** `cierres_caja.estado` es `varchar(20)`, tiene el CHECK `estado`, su `server_default` es `'pendiente'` y el tipo `estado_cierre` ya no existe en `pg_type`

#### Scenario: Datos existentes preservados

- **WHEN** la base tiene cierres con estado `pendiente`, `cerrado` o `reabierto` antes del upgrade
- **THEN** los valores se conservan como texto con el mismo contenido

#### Scenario: Downgrade restaura el ENUM

- **WHEN** se ejecuta `alembic downgrade` hasta `0014_pagos_simulados`
- **THEN** `estado` vuelve a ser del tipo `estado_cierre`, el tipo existe en `pg_type` y el CHECK de la columna deja de existir sin objetos huérfanos

#### Scenario: Sin multi-tenant

- **WHEN** se inspecciona la migración `0015`
- **THEN** no agrega `tenant_id` ni nuevas tablas (R2)
