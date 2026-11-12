# Spec Delta

## Purpose

Portal público unificado del consultorio: una cara sin login, con la marca única del consultorio, donde el paciente reserva un turno, consulta su reserva, revisa y aprueba su presupuesto y paga una seña o saldo simulado, todo sobre tokens opacos.

## ADDED Requirements

### Requirement: Rutas y marca única del portal

La SPA SHALL exponer las superficies públicas `/reservar`, `/p/turno/:token`, `/p/presupuesto/:token` y `/p/pagar/:token` sin autenticación y bajo una marca única del consultorio, sin `slug` ni segmento de tenant en la URL (R2).

#### Scenario: Acceso sin login

- **WHEN** un paciente abre cualquiera de las rutas públicas del portal
- **THEN** la SPA renderiza la vista sin pedir credenciales

#### Scenario: Marca única

- **WHEN** el paciente navega entre las superficies públicas
- **THEN** se muestra la misma marca del consultorio, sin selector de sucursal ni de tenant

#### Scenario: Ruta pública desconocida

- **WHEN** el paciente abre una ruta pública que no corresponde a ninguna vista
- **THEN** la SPA muestra una vista de "no encontrado" sin filtrar datos internos

### Requirement: Página pública de presupuesto

La SPA SHALL exponer `/p/presupuesto/:token` que consulte la vista pública del presupuesto por token y muestre sus ítems, total y estado en ARS, y SHALL ofrecer aprobar o rechazar el presupuesto con una firma simple (nombre del paciente) sobre un presupuesto en estado `enviado`.

#### Scenario: Presupuesto visible

- **WHEN** el paciente abre `/p/presupuesto/:token` con un token válido
- **THEN** la SPA muestra los ítems, el total en ARS y el estado actual

#### Scenario: Aprobación con firma

- **WHEN** el paciente ingresa su nombre y confirma la aprobación
- **THEN** la SPA invoca el endpoint de aprobación y refleja el estado `aprobado`

#### Scenario: Rechazo

- **WHEN** el paciente rechaza el presupuesto
- **THEN** la SPA invoca el endpoint de rechazo y refleja el estado `rechazado`

#### Scenario: Token inválido

- **WHEN** el token no corresponde a ningún presupuesto
- **THEN** la SPA muestra una vista de "no encontrado" genérica

### Requirement: Página de pago simulado y confirmación

La SPA SHALL exponer `/p/pagar/:token` que consulte el pago pendiente del presupuesto y permita confirmar el pago simulado, mostrando el monto en ARS y el resultado (aprobado o rechazado), y SHALL deshabilitar el botón de confirmación mientras la request está en curso.

#### Scenario: Pago confirmado

- **WHEN** el paciente confirma el pago simulado de un presupuesto aprobado
- **THEN** la SPA muestra la confirmación con el monto en ARS

#### Scenario: Doble clic no duplica

- **WHEN** el paciente vuelve a confirmar un pago ya aprobado
- **THEN** la SPA muestra el mismo resultado sin generar un segundo movimiento

#### Scenario: Pago no disponible

- **WHEN** el presupuesto no está aprobado o el token no existe
- **THEN** la SPA muestra un mensaje accionable en español rioplatense sin filtrar datos internos

### Requirement: Presentación del portal en es-AR

Las superficies del portal SHALL estar en español rioplatense y mostrar los montos en ARS (R10).

#### Scenario: Monto en ARS

- **WHEN** el portal muestra el total de un presupuesto o el monto de un pago
- **THEN** el monto se formatea en pesos argentinos

#### Scenario: Textos en rioplatense

- **WHEN** el paciente recorre las vistas del portal
- **THEN** los textos, botones y mensajes de error están en español rioplatense

### Requirement: Protección de datos en las superficies públicas

Las superficies y endpoints públicos del portal SHALL identificar los recursos solo por un token opaco no adivinable, responder 404 genérico ante un token inexistente y no exponer ni registrar datos sensibles de salud, DNI, teléfono ni IDs internos (R9).

#### Scenario: Token inexistente

- **WHEN** se consulta un recurso público con un token que no existe
- **THEN** la API responde 404 sin revelar si el recurso existió

#### Scenario: Respuesta sin PII ni IDs internos

- **WHEN** se consulta el presupuesto o el pago público por token
- **THEN** la respuesta no contiene `paciente_id`, `presupuesto_id` ni datos clínicos

#### Scenario: Sin datos sensibles en logs

- **WHEN** se procesa una request pública del portal
- **THEN** los logs no registran DNI, teléfono ni datos clínicos
