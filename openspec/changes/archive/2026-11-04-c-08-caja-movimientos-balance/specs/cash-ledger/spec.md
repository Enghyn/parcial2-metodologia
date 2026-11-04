# Spec Delta — cash-ledger

## Purpose

Define el libro append-only de caja del consultorio: registro de ingresos y egresos con usuario responsable, validación del turno vinculado, consulta diaria y resumen por medio de pago, sin updates ni deletes.

## ADDED Requirements

### Requirement: Registro de movimiento con usuario del token

El sistema SHALL exponer `POST /api/v1/caja/movimientos` para `admin` y `recepcion`, exigiendo `tipo` (`ingreso`/`egreso`), `medio_pago` del catálogo, `monto > 0` y `concepto` no vacío. El `usuario_id` SHALL tomarse del JWT y SHALL NOT aceptarse en el body.

#### Scenario: Ingreso registrado

- **WHEN** un usuario autorizado envía un ingreso válido
- **THEN** la API responde 201 con el movimiento y el `usuario_id` del token

#### Scenario: Monto no positivo

- **WHEN** se envía `monto = 0` o negativo
- **THEN** la API responde 422 y no persiste nada

#### Scenario: Usuario en el body

- **WHEN** el body incluye `usuario_id`
- **THEN** la API responde 422 por `extra="forbid"`

### Requirement: Turno vinculado válido

El sistema SHALL permitir `turno_id` opcional; si viene, el turno SHALL existir y tener `deleted_at` nulo. Un turno inexistente o borrado SHALL responder 404 sin crear el movimiento.

#### Scenario: Turno activo

- **WHEN** se registra un movimiento con un `turno_id` activo
- **THEN** el movimiento se asocia al turno

#### Scenario: Turno borrado

- **WHEN** se registra un movimiento con un turno con `deleted_at` no nulo
- **THEN** la API responde 404 y no persiste el movimiento

### Requirement: Listado diario de movimientos

El sistema SHALL exponer `GET /api/v1/caja/movimientos?fecha=YYYY-MM-DD` para `admin` y `recepcion`, devolviendo los movimientos del día calendario ART ordenados por fecha descendente.

#### Scenario: Día con movimientos

- **WHEN** se consulta una fecha con ingresos y egresos
- **THEN** la API devuelve ambos, del más reciente al más antiguo

#### Scenario: Día sin movimientos

- **WHEN** se consulta una fecha sin movimientos
- **THEN** la API devuelve una lista vacía

### Requirement: Resumen diario de caja

El sistema SHALL exponer `GET /api/v1/caja/resumen-diario?fecha=YYYY-MM-DD` para `admin` y `recepcion`, devolviendo totales de ingresos y egresos, balance neto y totales por cada medio de pago; sin `fecha` SHALL usar el día ART actual.

#### Scenario: Resumen con movimientos

- **WHEN** hay ingresos y egresos en el día
- **THEN** el balance es `ingresos - egresos` y cada medio tiene su total

#### Scenario: Resumen sin movimientos

- **WHEN** no hay movimientos en el día
- **THEN** todos los totales son cero y el balance es cero

### Requirement: Libro append-only y contra-asiento

El sistema SHALL NOT exponer `PATCH` ni `DELETE` sobre movimientos; una corrección SHALL registrarse como un movimiento nuevo de tipo opuesto, mismo monto y concepto aclaratorio, conservando ambos asientos.

#### Scenario: Corrección de un ingreso

- **WHEN** se detecta un error en un ingreso y se registra el egreso compensatorio
- **THEN** el libro conserva ambos movimientos y el balance refleja la corrección

#### Scenario: Intento de modificar

- **WHEN** se intenta actualizar o borrar un movimiento por la API
- **THEN** la ruta no existe o el sistema rechaza la operación

### Requirement: Seña registrada manualmente

El sistema SHALL tratar la seña como un ingreso explícito vinculado al turno cuando recepción la cobra; `Turno.sena_monto` SHALL NOT generar un movimiento automático al reservar.

#### Scenario: Seña cobrada

- **WHEN** recepción registra una seña con `turno_id` y concepto “Seña de reserva”
- **THEN** queda un ingreso en caja asociado al turno

#### Scenario: Reserva con seña

- **WHEN** se crea un turno con `sena_monto > 0` sin registrar el cobro
- **THEN** no aparece un movimiento de caja automático

### Requirement: RBAC de caja

El sistema SHALL permitir registro y consulta solo a `admin` y `recepcion`; un `odontologo` SHALL recibir 403 y una request sin token SHALL recibir 401, independientemente de lo que muestre el frontend (R8).

#### Scenario: Odontólogo en caja

- **WHEN** un usuario con rol `odontologo` llama a un endpoint de caja
- **THEN** la API responde 403

#### Scenario: Sin token

- **WHEN** se llama a caja sin token válido
- **THEN** la API responde 401

### Requirement: Pantalla de caja

La SPA SHALL exponer `/app/caja` con formulario de ingreso/egreso, selector opcional de turno, tabla del libro diario y tarjetas de balance en ARS, y SHALL reflejar el resumen del día.

#### Scenario: Registrar y ver el movimiento

- **WHEN** un usuario autorizado registra un ingreso
- **THEN** la tabla y las tarjetas se actualizan sin recargar manualmente

#### Scenario: Rol sin permiso

- **WHEN** un `odontologo` intenta abrir la caja
- **THEN** la UI no le ofrece la pantalla o muestra acceso restringido
