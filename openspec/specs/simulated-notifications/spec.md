# simulated-notifications Specification

## Purpose
Registra y simula envíos de notificaciones de turnos por WhatsApp click-to-chat, con plantillas y reintentos locales, sin Meta API.

## Requirements

### Requirement: Modelo de notificación

El sistema SHALL persistir `Notificacion` con turno_id, plantilla, destinatario, estado (pendiente/enviado/fallido) y fecha.

#### Scenario: Alta de notificación
- **WHEN** se crea una notificación
- **THEN** la API responde 201 con estado pendiente

### Requirement: Notificador simulado

El sistema SHALL proveer `NotificadorSimulado` que genera link `wa.me` y registra el envío en BD/consola.

#### Scenario: Generar link wa.me
- **WHEN** se envía una notificación
- **THEN** se genera un link `https://wa.me/...` con mensaje url-encoded

### Requirement: Plantillas

El sistema SHALL incluir plantillas de confirmación, recordatorio 24h, recordatorio 2h y lista de espera.

#### Scenario: Plantilla de confirmación
- **WHEN** se solicita la plantilla de confirmación
- **THEN** retorna texto con datos del turno

### Requirement: RBAC

El sistema SHALL permitir consulta a admin/recepcion/odontologo; envío a admin/recepcion; sin token SHALL responder 401.

#### Scenario: Odontólogo envía
- **WHEN** un odontólogo intenta enviar
- **THEN** la API responde 403
