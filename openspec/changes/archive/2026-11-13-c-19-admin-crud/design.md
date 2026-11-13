# Design

## Context
Ver proposal.md.

## Goals / Non-Goals
**Goals:** CRUDs de usuarios, sillones, profesionales con baja lógica.
**Non-Goals:** migración (usa tablas existentes).

## Decisions
- Ampliar módulo `admin`.
- Endpoints bajo `/api/v1/admin/*`.
- Baja lógica con `deleted_at` y `activo=false`.

## Risks / Trade-offs
- No desactivar último admin: validar en servicio.

## Migration Plan
- Sin migración.

## Open Questions
- (ninguna)