# Spec Delta — agenda (timezone hardening)

## ADDED Requirements

### Requirement: Día calendario en zona del consultorio

El sistema SHALL interpretar todo `datetime` sin `tzinfo` como hora del consultorio (`America/Argentina/Buenos_Aires`) y SHALL calcular el filtro `fecha` entre las 00:00 y las 24:00 de esa zona, no en UTC.

#### Scenario: Naive se interpreta como ART

- **WHEN** se envía `inicio = 2027-01-10T09:00:00` sin offset
- **THEN** el turno se persiste como `2027-01-10T12:00:00Z` (09:00 ART)

#### Scenario: Filtro de día ART

- **WHEN** se consulta `GET /api/v1/turnos?fecha=2027-01-10`
- **THEN** se incluyen los turnos desde `2027-01-10T00:00-03:00` hasta `2027-01-11T00:00-03:00`

#### Scenario: Turno de las 22:00 ART pertenece al día consultado

- **WHEN** existe un turno a las 22:00 ART del 2027-01-10
- **THEN** aparece en el filtro `fecha=2027-01-10` y no en `fecha=2027-01-11`

### Requirement: Recursos vigentes al crear un turno

El sistema SHALL rechazar la creación de un turno cuando el sillón, el profesional o el paciente no existan, estén inactivos o tengan `deleted_at` no nulo, respondiendo 404 con la forma única de error.

#### Scenario: Sillón con borrado lógico

- **WHEN** se intenta crear un turno con un `sillon_id` cuyo `deleted_at` no es nulo
- **THEN** la API responde 404 y no persiste el turno

#### Scenario: Profesional inactivo

- **WHEN** se intenta crear un turno con un profesional con `activo=False`
- **THEN** la API responde 404 y no persiste el turno

#### Scenario: Paciente con borrado lógico

- **WHEN** se intenta crear un turno con un paciente con `deleted_at` no nulo
- **THEN** la API responde 404 y no persiste el turno

### Requirement: Turnos con inicio futuro

El sistema SHALL rechazar la creación de un turno cuyo `inicio` sea anterior o igual al momento de la request, respondiendo 422 con la forma única de error.

#### Scenario: Fecha pasada rechazada

- **WHEN** se intenta crear un turno con `inicio` en el pasado
- **THEN** la API responde 422 y no persiste el turno
