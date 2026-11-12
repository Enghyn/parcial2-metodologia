# Design

## Context
Ver proposal.md. Mono-consultorio, RBAC backend, PK UUID, borrado lógico.

## Goals / Non-Goals
**Goals:** modelo Comprobante, Facturador interface + manual, endpoints emitir/anular.
**Non-Goals:** ARCA/AFIP, integración pagos.

## Decisions
- Módulo `comprobante` con models/service/router/schemas.
- Facturador como Protocol/ABC en service.
- Migración `0010`.

## Risks / Trade-offs
- Numeración manual puede duplicarse → unique constraint en número.

## Migration Plan
- Crear migración con tabla comprobantes y FKs.

## Open Questions
- (ninguna)