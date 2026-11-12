# Proposal

## Why

El consultorio necesita enviar confirmaciones y recordatorios de turnos por WhatsApp click-to-chat y registrar notificaciones simuladas en BD/consola. Hoy no existe el módulo.

## What Changes

- Interfaz `Notificador` + `NotificadorSimulado`.
- Plantillas de confirmación, recordatorio 24h/2h y lista de espera.
- Link `wa.me`; reintentos locales; sin Meta API.
- Modelo `Notificacion` (migración `0011`).
- Endpoints para listar/enviar notificaciones.

## Capabilities

### New Capabilities
- `simulated-notifications`: notificaciones simuladas por WhatsApp click-to-chat con plantillas y registro en BD.

### Modified Capabilities
- (ninguna)

## Impact

- Backend: nuevo módulo `notificaciones`, migración, tests.
- Dependencias: C-06, C-09a.