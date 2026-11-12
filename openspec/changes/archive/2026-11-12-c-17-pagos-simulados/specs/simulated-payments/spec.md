# Spec Delta

## Purpose

Registra pagos simulados con estados y confirmación idempotente que crea un MovimientoCaja real.

## ADDED Requirements

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