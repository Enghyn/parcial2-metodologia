# Spec Delta — agenda

## MODIFIED Requirements

### Requirement: Listado de turnos con filtros

El sistema SHALL exponer `GET /api/v1/turnos` para los roles `admin`, `recepcion` y `odontologo`, devolviendo solo turnos no borrados lógicamente y ordenados por `inicio` ascendente con desempate determinista. Acepta `fecha`, o el rango inclusivo `desde`/`hasta`, y los filtros opcionales `profesional_id` y `sillon_id`; `fecha` y el rango son mutuamente excluyentes.

#### Scenario: Filtrado por fecha

- **WHEN** se consulta con un parámetro `fecha`
- **THEN** solo se devuelven los turnos de ese día

#### Scenario: Filtrado por profesional y sillón

- **WHEN** se consulta con `profesional_id` o `sillon_id`
- **THEN** solo se devuelven los turnos que coinciden con el filtro

#### Scenario: Rango semanal en una sola consulta

- **WHEN** se consulta con `desde=2027-01-04` y `hasta=2027-01-10`
- **THEN** se devuelven en una única respuesta todos los turnos cuyo `inicio` cae entre las 00:00 ART del 4 y las 00:00 ART del 11, ambos extremos del rango incluidos

#### Scenario: Rango con un solo extremo rechazado

- **WHEN** se envía solo `desde` o solo `hasta`
- **THEN** la API responde 422 con la forma única de error y no devuelve turnos

#### Scenario: Rango invertido rechazado

- **WHEN** se envía `desde` posterior a `hasta`
- **THEN** la API responde 422 con la forma única de error

#### Scenario: Rango excesivo rechazado

- **WHEN** el rango solicitado supera los 31 días de calendario
- **THEN** la API responde 422 con la forma única de error

#### Scenario: Rango combinado con filtros de recurso

- **WHEN** se consulta un rango junto con `profesional_id` o `sillon_id`
- **THEN** se devuelven solo los turnos del rango que además coinciden con el recurso

#### Scenario: Orden determinista

- **WHEN** dos turnos del rango comparten el mismo `inicio`
- **THEN** el listado los devuelve en un orden estable entre llamadas

#### Scenario: Sin datos clínicos en logs ni en la URL

- **WHEN** se consulta un rango de turnos
- **THEN** la URL solo contiene fechas y filtros de recurso, y los logs de la aplicación no incluyen `prestacion` ni `notas` de los pacientes

### Requirement: Día calendario en zona del consultorio

El sistema SHALL interpretar todo `datetime` sin `tzinfo` como hora del consultorio (`America/Argentina/Buenos_Aires`) y SHALL calcular los filtros `fecha` y `desde`/`hasta` entre las 00:00 y las 24:00 de esa zona, no en UTC.

#### Scenario: Naive se interpreta como ART

- **WHEN** se envía `inicio = 2027-01-10T09:00:00` sin offset
- **THEN** el turno se persiste como `2027-01-10T12:00:00Z` (09:00 ART)

#### Scenario: Filtro de día ART

- **WHEN** se consulta `GET /api/v1/turnos?fecha=2027-01-10`
- **THEN** se incluyen los turnos desde `2027-01-10T00:00-03:00` hasta `2027-01-11T00:00-03:00`

#### Scenario: Turno de las 22:00 ART pertenece al día consultado

- **WHEN** existe un turno a las 22:00 ART del 2027-01-10
- **THEN** aparece en el filtro `fecha=2027-01-10` y no en `fecha=2027-01-11`

#### Scenario: Límites del rango en ART

- **WHEN** se consulta `desde=2027-01-04` y `hasta=2027-01-10`
- **THEN** el rango cubre desde `2027-01-04T00:00-03:00` hasta `2027-01-11T00:00-03:00` y un turno de las 23:30 ART del 10 aparece en la respuesta

#### Scenario: Turno del domingo anterior excluido

- **WHEN** existe un turno a las 23:30 ART del 2027-01-03 y se consulta `desde=2027-01-04`
- **THEN** ese turno no aparece en la respuesta
