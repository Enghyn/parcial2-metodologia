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
