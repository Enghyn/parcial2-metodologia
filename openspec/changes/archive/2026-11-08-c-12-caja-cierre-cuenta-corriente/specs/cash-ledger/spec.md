# Spec Delta — cash-ledger

## MODIFIED Requirements

### Requirement: Registro de movimiento con usuario del token

El sistema SHALL exponer `POST /api/v1/caja/movimientos` para `admin` y `recepcion`, exigiendo `tipo` (`ingreso`/`egreso`), `medio_pago` del catálogo, `monto > 0` y `concepto` no vacío. El `usuario_id` SHALL tomarse del JWT y SHALL NOT aceptarse en el body. Si la fecha del movimiento corresponde a un día con cierre aprobado (`cierres_caja` en estado `cerrado`), la API SHALL responder 409 y SHALL NOT crear el movimiento (bloqueo de período).

#### Scenario: Ingreso registrado

- **WHEN** un usuario autorizado envía un ingreso válido en un día sin cierre
- **THEN** la API responde 201 con el movimiento y el `usuario_id` del token

#### Scenario: Día cerrado bloquea movimiento

- **WHEN** el día tiene un cierre aprobado y se intenta registrar un movimiento con esa fecha
- **THEN** la API responde 409 y no persiste el movimiento

#### Scenario: Monto no positivo

- **WHEN** se envía `monto = 0` o negativo
- **THEN** la API responde 422 y no persiste nada

#### Scenario: Usuario en el body

- **WHEN** el body incluye `usuario_id`
- **THEN** la API responde 422 por `extra="forbid"`

## ADDED Requirements

### Requirement: Cierre diario aprobado por admin

El sistema SHALL exponer `POST /api/v1/caja/cierres` solo para `admin`, que calcule el balance del día calendario ART desde `movimientos_caja`, registre un `CierreCaja` con estado `cerrado`, `aprobado_por` y `aprobado_en`, y lo bloquee para nuevos movimientos de ese día. `GET /api/v1/caja/cierres` SHALL listar los cierres con su estado y balance para `admin` y `recepcion`.

#### Scenario: Admin cierra el día

- **WHEN** un `admin` solicita el cierre de un día con movimientos y sin cierre previo
- **THEN** la API responde 201 con el cierre, el balance calculado y el `aprobado_por` del token

#### Scenario: Día ya cerrado

- **WHEN** se intenta cerrar un día que ya tiene cierre aprobado
- **THEN** la API responde 409 y no crea un segundo cierre

#### Scenario: Recepción no puede cerrar

- **WHEN** un usuario con rol `recepcion` llama a `POST /cierres`
- **THEN** la API responde 403

### Requirement: Cuenta corriente por paciente

El sistema SHALL exponer `GET /api/v1/caja/cuenta-corriente/{pacienteId}` que devuelva el saldo derivado (suma de movimientos tipo ingreso menos egresos vinculados a turnos del paciente) y el detalle de esos movimientos, y `GET /api/v1/caja/cuentas-corrientes` que liste pacientes con saldo distinto de cero. Pacientes con `deleted_at` no nulo SHALL responder 404.

#### Scenario: Saldo derivado de movimientos

- **WHEN** un paciente tiene turnos con movimientos de ingreso y egreso
- **THEN** el saldo es `suma(ingresos) - suma(egresos)` y el detalle lista cada movimiento con fecha, medio y concepto

#### Scenario: Paciente sin movimientos

- **WHEN** se consulta la cuenta corriente de un paciente sin movimientos
- **THEN** el saldo es cero y el detalle está vacío

#### Scenario: Paciente dado de baja

- **WHEN** el paciente tiene `deleted_at` no nulo
- **THEN** la API responde 404

### Requirement: Ajustes auditados (contra-asiento con motivo)

El sistema SHALL registrar cada corrección contable como un contra-asiento (movimiento nuevo de tipo opuesto) vinculado a un `AjusteCaja` que registre `movimiento_corregido_id`, `movimiento_ajuste_id`, `motivo`, `fecha` y `usuario_aprobador_id` (solo `admin`). Nunca SHALL modificarse ni borrarse el movimiento original (RN-CJ-02).

#### Scenario: Ajuste aprobado por admin

- **WHEN** un `admin` registra un ajuste con motivo y contra-asiento
- **THEN** se crea una fila en `ajustes_caja` y el contra-asiento en `movimientos_caja`, conservando el original

#### Scenario: Recepción no puede ajustar

- **WHEN** un `recepcion` intenta registrar un ajuste
- **THEN** la API responde 403

### Requirement: Export CSV del libro y del cierre

El sistema SHALL exponer `GET /api/v1/caja/export?fecha=YYYY-MM-DD` (y opcionalmente para un cierre) que devuelva un archivo CSV (UTF-8, separador coma, montos en ARS) con las columnas del libro del día o del cierre: `fecha`, `tipo`, `medio_pago`, `monto`, `concepto`, `turno_id`, `usuario_id`. Solo `admin` y `recepcion`; nunca incluir datos clínicos ni de salud (R9).

#### Scenario: Export de un día

- **WHEN** un usuario autorizado solicita el CSV de una fecha con movimientos
- **THEN** la API devuelve `text/csv` con una fila por movimiento y los totales del día

#### Scenario: Export de cierre

- **WHEN** se solicita el CSV de un cierre aprobado
- **THEN** el archivo refleja los movimientos de ese día y el balance del cierre
