# Spec Delta — core-data-model

## ADDED Requirements

### Requirement: Tablas de cierre, cuenta corriente y ajustes

El sistema SHALL crear mediante la migración `0008_caja_cierre_cuenta_corriente` (encadenada a `0007_ficha_clinica_avanzada` y reversible con `downgrade`) las tablas `cierres_caja`, `cuentas_corrientes_paciente` y `ajustes_caja`, con sus índices, claves foráneas y check constraints, sin `tenant_id` (R2).

#### Sub-requirement: cierres_caja

`cierres_caja` SHALL tener: `id` (UUID PK), `fecha_dia` (Date, UNIQUE), `estado` (Enum: `pendiente`, `cerrado`, `reabierto`), `balance` (Numeric 10,2), `total_ingresos` (Numeric 10,2), `total_egresos` (Numeric 10,2), `aprobado_por` (FK opcional a `usuarios`), `aprobado_en` (timestamp nullable), `created_at`. Solo `admin` puede pasar un cierre a `cerrado`.

#### Scenario: Cierre con estado cerrado y aprobador

- **WHEN** se aplica la migración y se crea un cierre aprobado por admin
- **THEN** `cierres_caja` tiene `estado = cerrado`, `aprobado_por` no nulo y `aprobado_en` con fecha

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

### Requirement: Migración 0008 reversible

La migración `0008_caja_cierre_cuenta_corriente` SHALL crear las tres tablas con índices y FKs en `upgrade` y SHALL eliminarlas sin dejar objetos huérfanos en `downgrade`, encadenada a la última migración aplicada (`0007`).

#### Scenario: downgrade limpia las tablas

- **WHEN** se ejecuta `alembic downgrade` hasta antes de 0008
- **THEN** `cierres_caja`, `cuentas_corrientes_paciente` y `ajustes_caja` no existen y no hay objetos huérfanos
