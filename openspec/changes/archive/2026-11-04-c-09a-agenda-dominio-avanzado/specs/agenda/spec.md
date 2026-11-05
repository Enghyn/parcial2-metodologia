# Spec Delta — agenda (dominio avanzado)

## ADDED Requirements

### Requirement: Reprogramación de turno con antisolapamiento

El sistema SHALL exponer `PATCH /api/v1/turnos/{id}/reprogramar` para `admin` y `recepcion`, aceptando un nuevo `inicio` y opcionalmente `duracion_min`; SHALL recalcular `fin`, excluir el propio turno de la validación de solapamiento y SHALL rechazar con 409 si el nuevo rango choca con otro turno activo o bloqueo.

#### Scenario: Reprogramación exitosa

- **WHEN** se mueve un turno a un hueco libre manteniendo sillón y profesional
- **THEN** la API responde 200 con el nuevo `inicio`/`fin` y el turno conserva su identidad

#### Scenario: Reprogramación que choca con otro turno

- **WHEN** el nuevo rango se solapa con otro turno activo del mismo sillón o profesional
- **THEN** la API responde 409 y no modifica el turno

#### Scenario: Turno atendido no se reprograma

- **WHEN** se intenta reprogramar un turno en estado `atendido`, `cancelado` o `ausente`
- **THEN** la API responde 409

### Requirement: Sobreturno autorizado

El sistema SHALL exponer `POST /api/v1/turnos/sobreturno` solo para `admin` y `recepcion`, exigiendo `motivo_sobreturno` no vacío, tomando `autorizado_por` del JWT y permitiendo el solapamiento deliberado con otro turno.

#### Scenario: Sobreturno creado

- **WHEN** recepción crea un sobreturno con motivo en un horario ya ocupado
- **THEN** la API responde 201 y el turno queda marcado como sobreturno con el usuario autorizador

#### Scenario: Sobreturno sin motivo

- **WHEN** se intenta crear un sobreturno sin `motivo_sobreturno`
- **THEN** la API responde 422 y no persiste nada

#### Scenario: Turno normal en horario ocupado

- **WHEN** se crea un turno normal en un horario ocupado
- **THEN** la API responde 409, como antes

### Requirement: Estado ausente por no-show

El sistema SHALL incluir `ausente` en el catálogo de estados del turno y SHALL permitir marcarlo mediante `PATCH /api/v1/turnos/{id}/estado`; el turno SHALL conservar sus datos y no se borra.

#### Scenario: Marcar ausente

- **WHEN** un usuario autorizado marca un turno como `ausente`
- **THEN** la API responde 200 con el estado actualizado

#### Scenario: Estado fuera del catálogo

- **WHEN** se envía un estado distinto de los permitidos
- **THEN** la API responde 422
