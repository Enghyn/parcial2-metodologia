# Design

## Context

Ver `proposal.md` (motivación). El sistema es mono-consultorio (R2), sin tenant_id. Modelos SQLAlchemy + Alembic. RBAC en backend (R8). PK UUID con `gen_random_uuid()`. Borrado lógico en tablas de negocio (R13).

## Goals / Non-Goals

**Goals:**
- Modelar OS, convenios, nomenclador y afiliación.
- Calcular cobertura/copago de forma determinista y testeable.
- Endpoints REST con RBAC.

**Non-Goals:**
- Validación online contra OS reales (fuera de alcance).
- Facturación electrónica (C-13b).
- Integración con pagos (C-17).

## Decisions

- Módulos separados `os` (OS + convenios + afiliación) y `nomenclador` (prácticas + aranceles por convenio) para mantener cohesión.
- Tabla `nomenclador_practica` base + `convenio_practica` (override de arancel/copago) para no duplicar prácticas.
- Cobertura calculada en servicio puro (función) a partir de afiliación vigente y arancel vigente; sin side effects.
- Migración `0009` (confirmar número real con `alembic heads`).

## Risks / Trade-offs

- [Vigencia de convenios por fecha] → comparar `vigente_desde <= fecha <= vigente_hasta`; si `vigente_hasta` es null, sin fin.
- [Afiliación múltiple] → unique parcial por paciente con `vigente_hasta IS NULL` o lógica en servicio.
- [Arancel negativo] → check constraint `arancel >= 0`.

## Migration Plan

- Crear migración Alembic con las 4 tablas y FKs.
- `alembic upgrade head`.
- Seed opcional de OS de ejemplo (idempotente).

## Open Questions

- (ninguna bloqueante)