# Design

## Context
Ver proposal.md.

## Goals / Non-Goals
**Goals:** modelo, servicio de ofertas, endpoints.
**Non-Goals:** workers externos.

## Decisions
- Módulo `lista_espera`.
- Migración `0012`.
- Ofertas en servicio local.

## Risks / Trade-offs
- Concurrencia: ofertas secuenciales.

## Migration Plan
- Crear migración con tabla lista_espera y ofertas.

## Open Questions
- (ninguna)