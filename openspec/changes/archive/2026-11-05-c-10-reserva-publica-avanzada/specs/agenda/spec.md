# Spec Delta — agenda

## ADDED Requirements

### Requirement: Origen del turno en el contrato interno

`TurnoOut` SHALL incluir `origen` con valores `interno` o `publico`. Todo turno creado por `POST /api/v1/turnos` o `POST /api/v1/turnos/sobreturno` SHALL quedar con `origen = 'interno'`; solo el portal público SHALL poder crear turnos con `origen = 'publico'`, y ningún payload de cliente SHALL permitir fijar el origen.

#### Scenario: Listado interno expone el origen
- **WHEN** se consulta `GET /api/v1/turnos`
- **THEN** cada turno devuelve `origen` con `interno` o `publico`

#### Scenario: Creación interna queda como interna
- **WHEN** recepción crea un turno desde la agenda
- **THEN** el turno persistido tiene `origen = 'interno'`

#### Scenario: Reserva pública queda como pública
- **WHEN** un paciente reserva desde `/reservar`
- **THEN** el turno persistido tiene `origen = 'publico'` y la agenda interna lo muestra así

#### Scenario: El cliente no puede fijar el origen
- **WHEN** el cuerpo de `POST /api/v1/turnos` incluye `origen`
- **THEN** la API responde 422 y no persiste el turno

### Requirement: Las pre-reservas públicas no bloquean la agenda interna

Una pre-reserva pública SHALL NOT participar de la validación de antisolapamiento de `TurnoService`: la agenda interna SHALL poder crear un turno sobre un hueco retenido. La validación de RN-AG-01 SHALL seguir considerando únicamente turnos activos y bloqueos.

#### Scenario: Creación interna sobre un hueco retenido
- **WHEN** recepción crea un turno en un rango con una pre-reserva pública vigente
- **THEN** la API responde 201 y el turno se persiste

#### Scenario: El antisolapamiento no cambia
- **WHEN** dos turnos activos se solapan en el mismo sillón o profesional
- **THEN** la API sigue respondiendo 409 como antes de este change

#### Scenario: Las retenciones no aparecen en el listado interno
- **WHEN** se consulta `GET /api/v1/turnos`
- **THEN** la respuesta solo contiene turnos y ninguna pre-reserva
