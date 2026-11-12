# budgets Specification

## Purpose
Gestiona presupuestos odontológicos con ítems, total, cobertura OS/copago, estados y aprobación online con token.

## Requirements

### Requirement: Modelo de presupuesto

El sistema SHALL persistir `Presupuesto` con paciente, estado, total y token público, y `ItemPresupuesto` con práctica, cantidad, arancel y cobertura.

#### Scenario: Alta de presupuesto
- **WHEN** se crea un presupuesto con ítems
- **THEN** la API responde 201 con estado borrador

### Requirement: Estados

El sistema SHALL soportar estados borrador/enviado/aprobado/rechazado/cobrado con transiciones válidas.

#### Scenario: Enviar presupuesto
- **WHEN** se envía un presupuesto borrador
- **THEN** el estado pasa a enviado

### Requirement: Aprobación online

El sistema SHALL exponer endpoint público con token para aprobar/rechazar el presupuesto.

#### Scenario: Aprobar con token
- **WHEN** se aprueba con token válido
- **THEN** el estado pasa a aprobado

### Requirement: RBAC

El sistema SHALL permitir gestión a admin/recepcion/odontologo; sin token SHALL responder 401.

#### Scenario: Sin token
- **WHEN** se llama sin token
- **THEN** la API responde 401
