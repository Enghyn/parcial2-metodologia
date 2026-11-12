# waitlist Specification

## Purpose
Gestiona lista de espera con preferencias y ofrece automáticamente turnos liberados al cancelar, con expiración y aceptación.

## Requirements

### Requirement: Modelo de lista de espera

El sistema SHALL persistir `ListaEspera` con paciente, preferencias (profesional/sillón/fecha), estado y fecha de ingreso.

#### Scenario: Alta en lista
- **WHEN** se agrega un paciente a la lista
- **THEN** la API responde 201 con estado pendiente

### Requirement: Orden por compatibilidad

El sistema SHALL ordenar candidatos por compatibilidad con el hueco liberado y antigüedad.

#### Scenario: Orden correcto
- **WHEN** se liberan huecos
- **THEN** se ofrece al candidato más compatible y antiguo

### Requirement: Oferta con expiración

El sistema SHALL generar una oferta con fecha de expiración; si no se acepta, pasa al siguiente.

#### Scenario: Oferta expirada
- **WHEN** la oferta expira sin aceptación
- **THEN** se ofrece al siguiente candidato

### Requirement: Aceptación

El sistema SHALL permitir aceptar la oferta y crear el turno.

#### Scenario: Aceptar oferta
- **WHEN** el paciente acepta
- **THEN** se crea el turno y se cierra la oferta

### Requirement: RBAC

El sistema SHALL permitir gestión a admin/recepcion; sin token SHALL responder 401.

#### Scenario: Sin token
- **WHEN** se llama sin token
- **THEN** la API responde 401
