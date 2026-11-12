# Proposal

## Why

El consultorio necesita emitir comprobantes manuales (recibos) vinculados a movimientos de caja y presupuestos, sin integración con ARCA/AFIP. Hoy no existe el modelo ni el flujo.

## What Changes

- Modelo `Comprobante` con estado pendiente/emitido/anulado y numeración manual.
- Interfaz `Facturador` + `FacturadorManual`.
- Endpoints para emitir/anular comprobantes (admin/recepcion).
- RBAC y trazabilidad.

## Capabilities

### New Capabilities
- `manual-receipt`: emisión y anulación de comprobantes manuales vinculados a movimientos/presupuestos.

### Modified Capabilities
- (ninguna)

## Impact

- Backend: nuevo módulo `comprobante`, migración, tests.
- Dependencias: C-13a, C-12.