# Proposal

## Why

El consultorio necesita gestionar lista de espera con preferencias y ofrecer turnos liberados automáticamente al cancelar, notificando al paciente. Hoy no existe.

## What Changes

- Modelo `ListaEspera`.
- Orden por compatibilidad/antigüedad.
- Oferta automática con expiración y aceptación.
- Usa notificaciones simuladas.
- Migración `0012`.

## Capabilities

### New Capabilities
- `waitlist`: lista de espera con ofertas automáticas de turnos liberados.

### Modified Capabilities
- (ninguna)

## Impact

- Backend: nuevo módulo `lista_espera`, migración, tests.
- Dependencias: C-09a, C-10, C-14.