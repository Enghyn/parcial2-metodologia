# manual-receipt Specification

## Purpose
Permite emitir y anular comprobantes manuales vinculados a movimientos de caja o presupuestos, con numeración manual y estado, sin integración con ARCA/AFIP.

## Requirements

### Requirement: Modelo de comprobante

El sistema SHALL persistir `Comprobante` con movimiento_id (opcional), presupuesto_id (opcional), número manual, estado (pendiente/emitido/anulado), fecha emisión y usuario emisor.

#### Scenario: Alta de comprobante
- **WHEN** se crea un comprobante con número manual
- **THEN** la API responde 201 con estado pendiente

### Requirement: Emisión y anulación

El sistema SHALL exponer endpoints para emitir (pendiente→emitido) y anular (emitido→anulado) comprobantes, solo admin/recepcion. Anular no borra el comprobante.

#### Scenario: Emitir comprobante
- **WHEN** un usuario autorizado emite un comprobante pendiente
- **THEN** el estado pasa a emitido y se registra fecha/usuario

#### Scenario: Anular comprobante
- **WHEN** se anula un comprobante emitido
- **THEN** el estado pasa a anulado y se conserva el registro

### Requirement: Facturador manual

El sistema SHALL proveer interfaz `Facturador` con implementación `FacturadorManual` que genera comprobantes sin validación externa.

#### Scenario: Facturador manual
- **WHEN** se solicita emisión por FacturadorManual
- **THEN** se crea un comprobante con número manual

### Requirement: RBAC

El sistema SHALL permitir gestión solo a admin/recepcion; consulta a admin/recepcion/odontologo; sin token SHALL responder 401.

#### Scenario: Odontólogo emite
- **WHEN** un odontólogo intenta emitir
- **THEN** la API responde 403
