# Proposal

## Why

El consultorio necesita registrar pagos simulados con estados pendiente/aprobado/rechazado, confirmación idempotente que crea un MovimientoCaja real. Hoy no existe.

## What Changes

- Modelos `Pago` e `IntentoPago`.
- Interfaz `Cobrador` + `CobradorSimulado`.
- Confirmación idempotente crea un MovimientoCaja.
- Migración `0014`.

## Capabilities

### New Capabilities
- `simulated-payments`: pagos simulados con confirmación idempotente y movimiento de caja.

### Modified Capabilities
- (ninguna)

## Impact

- Backend: nuevo módulo `pagos`, migración, tests.
- Dependencias: C-12, C-16.