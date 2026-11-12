# simulated-payments Specification

## Purpose
Registra pagos simulados con estados y confirmación idempotente que crea un MovimientoCaja real.

## Requirements

### Requirement: Modelo de pago

El sistema SHALL persistir `Pago` con presupuesto_id, monto, estado y `IntentoPago` con resultado.

#### Scenario: Alta de pago
- **WHEN** se crea un pago
- **THEN** la API responde 201 con estado pendiente

### Requirement: Confirmación idempotente

El sistema SHALL confirmar un pago una sola vez y crear un único MovimientoCaja.

#### Scenario: Confirmar pago
- **WHEN** se confirma un pago pendiente
- **THEN** el estado pasa a aprobado y se crea un movimiento de caja

#### Scenario: Doble confirmación
- **WHEN** se confirma un pago ya aprobado
- **THEN** no se crea un segundo movimiento

### Requirement: Cobrador simulado

El sistema SHALL proveer `CobradorSimulado` sin integración externa.

#### Scenario: Cobrador simulado
- **WHEN** se procesa un pago
- **THEN** retorna aprobado sin llamada externa

### Requirement: RBAC

El sistema SHALL permitir gestión a admin/recepcion; sin token SHALL responder 401.

#### Scenario: Sin token
- **WHEN** se llama sin token
- **THEN** la API responde 401

### Requirement: Confirmación pública desde el portal

El sistema SHALL exponer `POST /api/v1/public/pagos/{token}/confirmar`, donde `{token}` es el `token_publico` del presupuesto, que resuelva el pago pendiente de ese presupuesto (creándolo por el monto adeudado si no existe), lo confirme a través del cobrador simulado y cree **un** `MovimientoCaja` de ingreso con medio de pago, concepto y usuario responsable (R3/R4); un presupuesto no aprobado SHALL responder 409 y un token inexistente SHALL responder 404. La confirmación SHALL ser idempotente: repetirla sobre un pago ya `aprobado` devuelve el mismo resultado sin crear un segundo movimiento, incluso ante requests concurrentes.

#### Scenario: Confirmación desde el portal

- **WHEN** se confirma desde el portal un presupuesto `aprobado` con pago pendiente
- **THEN** el pago pasa a `aprobado` y se crea un único `MovimientoCaja`

#### Scenario: Doble confirmación

- **WHEN** se confirma un pago que ya está `aprobado`
- **THEN** no se crea un segundo `MovimientoCaja` y la respuesta es la misma

#### Scenario: Confirmaciones concurrentes

- **WHEN** llegan dos confirmaciones simultáneas para el mismo presupuesto
- **THEN** se crea exactamente un `MovimientoCaja`

#### Scenario: Presupuesto no aprobado

- **WHEN** se intenta confirmar el pago de un presupuesto en estado `enviado`
- **THEN** la API responde 409

#### Scenario: Token inexistente

- **WHEN** se confirma con un token que no existe
- **THEN** la API responde 404

#### Scenario: Sin IDs internos

- **WHEN** se devuelve el resultado de la confirmación pública
- **THEN** la respuesta no incluye `id`, `presupuesto_id` ni `movimiento_id`
