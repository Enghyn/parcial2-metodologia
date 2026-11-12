# Design

## Context
Ver proposal.md.

## Goals / Non-Goals
**Goals:** módulo notificaciones, modelo, NotificadorSimulado, plantillas, endpoints.
**Non-Goals:** Meta API, workers externos.

## Decisions
- Módulo `notificaciones`.
- Migración `0011`.
- Reintentos locales en servicio.

## Risks / Trade-offs
- Envío simulado no entrega real; solo registro.

## Migration Plan
- Crear migración con tabla notificaciones.

## Open Questions
- (ninguna)