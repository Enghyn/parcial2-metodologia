# Spec Delta — public-reservation (patient privacy)

## MODIFIED Requirements

### Requirement: Find-or-create de paciente por DNI

El sistema SHALL reutilizar un `Paciente` activo existente cuyo DNI coincida con el de la reserva **sin modificar** sus datos de contacto; SHALL crear uno nuevo solo si no existe; y si el DNI pertenece a una ficha con borrado lógico SHALL responder 409 sin reactivarla ni exponer datos sensibles.

#### Scenario: Paciente existente reutilizado

- **WHEN** se reserva con un DNI ya registrado y un teléfono o email distintos a los almacenados
- **THEN** el turno se asocia al paciente existente, no se crea un duplicado y sus datos de contacto no cambian

#### Scenario: Paciente nuevo creado

- **WHEN** se reserva con un DNI no registrado
- **THEN** se crea un nuevo `Paciente` con los datos enviados y el turno se asocia a él

#### Scenario: DNI de ficha borrada lógicamente

- **WHEN** se reserva con el DNI de un paciente que tiene `deleted_at` no nulo
- **THEN** la API responde 409 con un mensaje que invita a contactar al consultorio, sin reactivar la ficha ni modificarla

#### Scenario: Email opcional no borra el existente

- **WHEN** se reserva con un DNI existente sin enviar email
- **THEN** el email almacenado del paciente permanece intacto
