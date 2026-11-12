# Proposal

## Why

El consultorio necesita crear presupuestos con ítems, total y cobertura OS/copago, estados y aprobación online con token. Hoy no existe.

## What Changes

- Modelos `Presupuesto` e `ItemPresupuesto`.
- Estados borrador/enviado/aprobado/rechazado/cobrado.
- Aprobación online con token y firma simple.
- Migración `0013`.

## Capabilities

### New Capabilities
- `budgets`: presupuestos con ítems, total, cobertura y aprobación online.

### Modified Capabilities
- (ninguna)

## Impact

- Backend: nuevo módulo `presupuestos`, migración, tests.
- Dependencias: C-11, C-12, C-13a.