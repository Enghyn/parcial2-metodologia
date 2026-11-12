# Design

## Context
Ver proposal.md.

## Goals / Non-Goals
**Goals:** modelos, CobradorSimulado, confirmación idempotente, endpoints.
**Non-Goals:** Mercado Pago real.

## Decisions
- Módulo `pagos`.
- Migración `0014`.
- Idempotencia por estado del pago.

## Risks / Trade-offs
- Doble confirmación debe ser segura.

## Migration Plan
- Crear migración con tablas pagos e intentos.

## Open Questions
- (ninguna)