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

El sistema SHALL exponer endpoints públicos con token para aprobar (`POST /api/v1/public/presupuestos/{token}/aprobar`) o rechazar (`POST /api/v1/public/presupuestos/{token}/rechazar`) un presupuesto en estado `enviado`, registrando la fecha de aprobación y respondiendo con la vista pública mínima; SHALL rechazar con 409 una transición inválida (por ejemplo aprobar o rechazar un presupuesto `cobrado`) y SHALL responder 404 ante un token inexistente. La aprobación SHALL ser idempotente: repetirla sobre un presupuesto ya `aprobado` no cambia el estado ni genera efectos adicionales.

#### Scenario: Aprobar con token

- **WHEN** se aprueba con token válido un presupuesto en estado `enviado`
- **THEN** el estado pasa a `aprobado` y se registra la fecha de aprobación

#### Scenario: Rechazar con token

- **WHEN** se rechaza con token válido un presupuesto en estado `enviado`
- **THEN** el estado pasa a `rechazado`

#### Scenario: Aprobación repetida

- **WHEN** se aprueba un presupuesto que ya está `aprobado`
- **THEN** la API responde 200 con el mismo estado sin efectos adicionales

#### Scenario: Transición inválida

- **WHEN** se aprueba o rechaza un presupuesto en estado `cobrado`
- **THEN** la API responde 409

#### Scenario: Token inexistente

- **WHEN** se aprueba o rechaza con un token que no existe
- **THEN** la API responde 404

### Requirement: RBAC

El sistema SHALL permitir gestión a admin/recepcion/odontologo; sin token SHALL responder 401.

#### Scenario: Sin token
- **WHEN** se llama sin token
- **THEN** la API responde 401

### Requirement: Vista pública mínima del presupuesto

El sistema SHALL exponer `GET /api/v1/public/presupuestos/{token}` que devuelva los ítems (descripción, cantidad, arancel y copago), el total y el estado del presupuesto identificado por su `token_publico`, sin IDs internos ni datos del paciente; un token inexistente SHALL responder 404.

#### Scenario: Token válido

- **WHEN** se consulta la vista pública con un `token_publico` existente
- **THEN** la API responde 200 con los ítems, el total y el estado

#### Scenario: Token inexistente

- **WHEN** se consulta con un token que no existe
- **THEN** la API responde 404 sin datos internos

#### Scenario: Sin IDs internos

- **WHEN** se devuelve la vista pública del presupuesto
- **THEN** la respuesta no incluye `id`, `paciente_id` ni `token_publico`
