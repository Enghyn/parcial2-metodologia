# public-reservation Specification

## Purpose
Portal público para que un paciente auto-agende un turno sin login: consulta de huecos libres cruzando sillones y profesionales, reserva que crea el turno en estado `reservado` con token público, consulta y cancelación por token opaco, y enlace Click-to-Chat de WhatsApp (RN-G-01). Reusa `TurnoService` para no duplicar el antisolapamiento (R6).

## Requirements

### Requirement: Endpoints públicos sin autenticación

El sistema SHALL exponer bajo `/api/v1/public/*` los endpoints `GET /disponibilidad`, `POST /reservar`, `GET /turnos/{token}` y `POST /turnos/{token}/cancelar` sin requerir cabecera `Authorization`, y SHALL validar toda entrada con schemas Pydantic `extra="forbid"` (RN-SEG-01, R8).

#### Scenario: Acceso sin token exitoso
- **WHEN** un cliente llama a cualquiera de los endpoints públicos sin token
- **THEN** la API procesa la request y no responde 401

#### Scenario: Campo extra rechazado
- **WHEN** el cuerpo de `POST /reservar` incluye un campo no declarado
- **THEN** la API responde 422

### Requirement: Consulta de disponibilidad de huecos libres

El sistema SHALL exponer `GET /api/v1/public/disponibilidad` que reciba `fecha` (date), `duracion_min` (int > 0, default 30) y `profesional_id` opcional, y devuelva la lista de slots libres (inicio ISO, profesional y sillón asignados) cruzando sillones y profesionales activos, ordenados por inicio.

#### Scenario: Huecos para cualquier profesional
- **WHEN** se consulta disponibilidad sin `profesional_id` para una fecha con capacidad libre
- **THEN** la API devuelve al menos un slot con `profesional_id` y `sillon_id` asignados

#### Scenario: Sin capacidad
- **WHEN** todos los sillones y profesionales están ocupados en la jornada
- **THEN** la API devuelve una lista vacía

#### Scenario: Parámetro fecha faltante
- **WHEN** se omite `fecha`
- **THEN** la API responde 422

### Requirement: Cálculo de slots reusa antisolapamiento

El sistema SHALL calcular los slots libres reutilizando la lógica de solapamiento de `TurnoService` (turnos activos no cancelados ni borrados lógicamente y bloqueos), excluyendo rangos ocupados por sillón o profesional, dentro de la jornada laboral configurable (default 08:00–20:00, grilla 30 min).

#### Scenario: Turno cancelado libera el slot
- **WHEN** existe un turno cancelado en un rango
- **THEN** ese rango puede aparecer como slot libre

#### Scenario: Bloqueo excluye el slot
- **WHEN** existe un bloqueo para un sillón en un rango
- **THEN** ningún slot que use ese sillón en ese rango se devuelve

### Requirement: Reserva pública crea turno reservado con token

El sistema SHALL exponer `POST /api/v1/public/reservar` que, con datos válidos, cree un `Turno` en estado `reservado` con `token_publico` generado, asignando `sillon_id` y `profesional_id` provistos, y devuelva los datos públicos del turno incluyendo el token.

#### Scenario: Reserva exitosa
- **WHEN** se envía una reserva válida en un hueco libre
- **THEN** la API responde 201 con el turno en estado `reservado` y un `token` no nulo

#### Scenario: Reserva en hueco ocupado
- **WHEN** se intenta reservar un turno que se solapa con uno activo
- **THEN** la API responde 409

#### Scenario: Campos obligatorios faltantes
- **WHEN** faltan `paciente.nombre`, `paciente.dni` o `paciente.telefono`
- **THEN** la API responde 422

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

### Requirement: Vista pública de turno por token

El sistema SHALL exponer `GET /api/v1/public/turnos/{token}` que devuelva los datos públicos del turno (prestación, inicio, fin, estado, nombres de paciente/profesional/sillón) sin IDs internos ni DNI/teléfono; un token inexistente SHALL responder 404.

#### Scenario: Token válido
- **WHEN** se consulta con un token existente
- **THEN** la API responde 200 con los datos públicos del turno

#### Scenario: Token inexistente
- **WHEN** se consulta con un token que no existe
- **THEN** la API responde 404

### Requirement: Cancelación autónoma por token

El sistema SHALL exponer `POST /api/v1/public/turnos/{token}/cancelar` que, si el turno está en estado `reservado` o `confirmado`, lo marque como `cancelado` (sin borrado físico, R13) y responda 200; si está en otro estado SHALL responder 409; si el token no existe SHALL responder 404.

#### Scenario: Cancelación exitosa
- **WHEN** se cancela un turno en estado `reservado`
- **THEN** el turno queda en estado `cancelado` y la API responde 200

#### Scenario: Cancelación no permitida
- **WHEN** se cancela un turno en estado `atendido`
- **THEN** la API responde 409

#### Scenario: Token inexistente
- **WHEN** se cancela con un token que no existe
- **THEN** la API responde 404

### Requirement: No exposición de datos sensibles en público

El sistema SHALL no incluir DNI, teléfono ni email del paciente en las respuestas públicas ni en parámetros de URL (excepto el token opaco), y SHALL no registrar datos sensibles en logs (R9).

#### Scenario: Respuesta sin DNI
- **WHEN** se consulta un turno público
- **THEN** la respuesta no contiene el campo `dni` ni `telefono`

### Requirement: Wizard de reserva en frontend

La SPA SHALL exponer `/reservar` con un asistente de 4 pasos (1. Prestación → 2. Profesional → 3. Día/Hora libre → 4. Datos del paciente) sin autenticación, consumiendo los endpoints públicos, y SHALL mostrar la confirmación al finalizar.

#### Scenario: Flujo completo
- **WHEN** el paciente completa los 4 pasos con datos válidos
- **THEN** la SPA crea la reserva y navega a la vista de confirmación

#### Scenario: Error de reserva
- **WHEN** el backend responde 409 o 422
- **THEN** la SPA muestra el mensaje de error y permanece en el paso actual

### Requirement: Vista de confirmación con enlace WhatsApp

La SPA SHALL exponer `/p/turno/:token` mostrando los datos del turno y un botón "Enviar aviso por WhatsApp" que abra `https://wa.me/<telefono>?text=<mensaje>` en una nueva pestaña (`target="_blank"`, `rel="noopener"`) con mensaje prearmado en es-AR, usando el teléfono configurado (RN-G-01, R10).

#### Scenario: Botón WhatsApp
- **WHEN** el usuario activa el botón de WhatsApp
- **THEN** se abre una nueva pestaña con la URL `wa.me` y el mensaje prearmado

#### Scenario: Cancelación desde la vista
- **WHEN** el usuario activa "Cancelar turno"
- **THEN** la SPA invoca el endpoint de cancelación y refleja el estado cancelado

### Requirement: Presentación en es-AR

Las superficies públicas SHALL estar en español rioplatense y los montos en ARS (R10).

#### Scenario: Idioma de superficie
- **WHEN** un paciente accede al portal público
- **THEN** los textos se muestran en español rioplatense

### Requirement: Disponibilidad pública en ART

El sistema SHALL generar los slots de `GET /api/v1/public/disponibilidad` en `America/Argentina/Buenos_Aires`, exponerlos como instantes UTC correctos y SHALL omitir los slots cuyo inicio ya pasó.

#### Scenario: Slot de las 09:00 ART

- **WHEN** se consulta disponibilidad para un día con capacidad a las 09:00 ART
- **THEN** el slot se serializa como `12:00:00Z` y el portal lo muestra como `09:00`

#### Scenario: Slot pasado excluido

- **WHEN** se consulta la disponibilidad del día actual después de las 09:00 ART
- **THEN** el slot de las 09:00 no se devuelve

### Requirement: Confirmación pública en ART

La vista `/p/turno/:token` SHALL mostrar la fecha y la hora del turno en `America/Argentina/Buenos_Aires`, independientemente de la zona del navegador.

#### Scenario: Confirmación de las 09:00 ART

- **WHEN** el turno tiene `inicio = 2027-01-10T12:00:00Z`
- **THEN** la confirmación muestra `09:00` y la fecha del 10 de enero de 2027

### Requirement: Ventana mínima de cancelación pública

El sistema SHALL rechazar con 409 la cancelación pública de un turno cuando falte menos que `cancelacion_min_horas` (default 12) para su `inicio`, y SHALL permitir la cancelación dentro de la ventana. La recepción SHALL poder cancelar con override desde la agenda interna.

#### Scenario: Cancelación dentro de la ventana

- **WHEN** el paciente cancela un turno que comienza en 24 h
- **THEN** la API responde 200 y el turno queda `cancelado`

#### Scenario: Cancelación fuera de la ventana

- **WHEN** el paciente cancela un turno que comienza en 2 h
- **THEN** la API responde 409 y el turno no cambia

#### Scenario: Override de recepción

- **WHEN** recepción cancela un turno fuera de la ventana desde la agenda interna
- **THEN** la API permite la cancelación
