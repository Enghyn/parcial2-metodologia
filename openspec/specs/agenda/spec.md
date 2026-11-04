# agenda Specification

## Purpose
Gestión de la agenda de turnos y bloqueos del consultorio: validación de antisolapamiento cruzado, cálculo de horarios, estados del turno y endpoints internos protegidos por RBAC.

## Requirements

### Requirement: Antisolapamiento cruzado de turnos

El sistema SHALL rechazar la creación o reprogramación de un turno cuando el sillón asignado O el profesional asignado ya tengan un turno activo (no cancelado ni borrado lógicamente) que se solape en el rango horario, respondiendo 409.

#### Scenario: Solapamiento en el mismo sillón

- **WHEN** se intenta crear un turno en un sillón y rango horario que ya ocupa otro turno activo del mismo sillón
- **THEN** la API responde 409 con la forma única de error

#### Scenario: Solapamiento del mismo profesional en distinto sillón

- **WHEN** se intenta crear un turno para un profesional que ya tiene un turno activo solapado en otro sillón
- **THEN** la API responde 409 con la forma única de error

#### Scenario: Mismo horario con sillón y profesional distintos

- **WHEN** se crean dos turnos en el mismo rango horario pero con sillón y profesional distintos
- **THEN** ambos se aceptan con respuesta exitosa

#### Scenario: Creación sobre un turno previamente cancelado

- **WHEN** se crea un turno en el mismo sillón, profesional y rango horario de un turno en estado `cancelado`
- **THEN** la creación es exitosa

### Requirement: Turnos cancelados excluidos de la disponibilidad

El sistema SHALL excluir los turnos en estado `cancelado` del cálculo de disponibilidad y del antisolapamiento, liberando de inmediato el sillón y el profesional.

#### Scenario: Cancelación libera el recurso

- **WHEN** un turno se marca como `cancelado`
- **THEN** un nuevo turno puede ocupar el mismo sillón, profesional y rango horario

### Requirement: Borrado lógico filtrado en agenda

El sistema SHALL filtrar `deleted_at IS NULL` en todas las consultas y validaciones de agenda, de modo que los turnos y recursos borrados lógicamente no bloqueen disponibilidad ni aparezcan en los listados.

#### Scenario: Turno borrado lógicamente no bloquea

- **WHEN** un turno tiene `deleted_at` no nulo
- **THEN** no se considera en el antisolapamiento ni se devuelve en `GET /api/v1/turnos`

### Requirement: Cálculo automático de fin

El sistema SHALL calcular `fin` automáticamente como `inicio + duracion_min` minutos, persistiendo ambos valores y cumpliendo `fin > inicio` y la coherencia entre duración y rango.

#### Scenario: Fin derivado de la duración

- **WHEN** se crea un turno con `inicio` e `duracion_min` válidos
- **THEN** el turno persistido tiene `fin = inicio + duracion_min` minutos

### Requirement: Asignación física obligatoria del turno

El sistema SHALL exigir `paciente_id`, `profesional_id`, `sillon_id`, `prestacion`, `inicio` y `duracion_min` (> 0) para crear un turno; la falta de alguno SHALL responder 422.

#### Scenario: Turno sin sillón rechazado

- **WHEN** se intenta crear un turno sin `sillon_id`
- **THEN** la API responde 422

### Requirement: Bloqueos como ocupación

El sistema SHALL tratar los bloqueos activos (no borrados lógicamente) como ocupación a efectos de disponibilidad: un turno no puede crearse en un rango bloqueado para el mismo sillón o profesional, y los bloqueos se crean/eliminan vía endpoints dedicados.

#### Scenario: Turno en rango bloqueado rechazado

- **WHEN** se intenta crear un turno en un rango bloqueado para el mismo sillón o profesional
- **THEN** la API responde 409

#### Scenario: Creación y eliminación de bloqueo

- **WHEN** un usuario autorizado crea un bloqueo válido y luego lo elimina
- **THEN** el bloqueo queda registrado y su eliminación lo retira de la disponibilidad

### Requirement: Listado de turnos con filtros

El sistema SHALL exponer `GET /api/v1/turnos` que devuelva los turnos no borrados lógicamente, admitiendo filtros opcionales por `fecha`, `profesional_id` y `sillon_id`, para los roles `admin`, `recepcion` y `odontologo`.

#### Scenario: Filtrado por fecha

- **WHEN** se consulta con un parámetro `fecha`
- **THEN** solo se devuelven los turnos de ese día

#### Scenario: Filtrado por profesional y sillón

- **WHEN** se consulta con `profesional_id` o `sillon_id`
- **THEN** solo se devuelven los turnos que coinciden con el filtro

### Requirement: Creación de turno

El sistema SHALL exponer `POST /api/v1/turnos` para crear un turno, aplicando la validación de antisolapamiento y el cálculo automático de `fin`, accesible a los roles `admin` y `recepcion`.

#### Scenario: Creación exitosa en hueco libre

- **WHEN** un usuario autorizado crea un turno en un hueco libre válido
- **THEN** la API responde 201 con el turno creado

### Requirement: Cambio de estado del turno

El sistema SHALL exponer `PATCH /api/v1/turnos/{id}/estado` para actualizar el estado del turno a uno del catálogo permitido, accesible a los roles `admin`, `recepcion` y `odontologo`; un turno inexistente o borrado lógicamente SHALL responder 404.

#### Scenario: Cambio de estado exitoso

- **WHEN** un usuario autorizado cambia el estado de un turno existente a un valor válido
- **THEN** la API responde 200 con el turno actualizado

#### Scenario: Turno inexistente

- **WHEN** se intenta cambiar el estado de un turno que no existe o está borrado lógicamente
- **THEN** la API responde 404

### Requirement: Endpoints de bloqueos

El sistema SHALL exponer `POST /api/v1/bloqueos` y `DELETE /api/v1/bloqueos/{id}`, accesibles a los roles `admin` y `recepcion`; un bloqueo inexistente SHALL responder 404 al eliminarlo.

#### Scenario: Eliminación de bloqueo inexistente

- **WHEN** se intenta eliminar un bloqueo que no existe
- **THEN** la API responde 404

### Requirement: Contrato de errores de agenda

El sistema SHALL responder con la forma única `{error:{code,message}}`: 409 para solapamiento o bloqueo, 404 para recurso inexistente, 422 para cuerpo inválido, 401/403 para fallos de autenticación/autorización.

#### Scenario: Cuerpo con campo extra rechazado

- **WHEN** el cuerpo de una request de agenda incluye un campo no declarado
- **THEN** la API responde 422

### Requirement: RBAC en backend para agenda

El sistema SHALL validar token y rol en el backend para cada endpoint de agenda; el frontend solo oculta o deshabilita la UI de manera cosmética (R8).

#### Scenario: Acceso sin token

- **WHEN** se llama a un endpoint de agenda sin token válido
- **THEN** la API responde 401

#### Scenario: Rol insuficiente

- **WHEN** un rol no admitido intenta una operación restringida (por ejemplo `odontologo` creando un turno)
- **THEN** la API responde 403
