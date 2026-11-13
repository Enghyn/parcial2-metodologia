# Proposal

## Why

Hoy el sistema no deja rastro de quién hizo qué y cuándo en las escrituras sensibles (turnos, caja, presupuestos, odontograma). Ante un reclamo o una inconsistencia clínica/contable no hay forma de reconstruir el hecho: no hay tabla `Auditoria`, ni hooks, ni visor, ni export. C-20 cierra esa brecha y materializa RN-SEG-01 (datos sensibles de salud fuera de logs y de parámetros de URL) también en la capa de auditoría: el `diff` y el CSV se enmascaran antes de persistir/exportar.

## What Changes

- Nueva migración reversible `0016_auditoria` (encadenada a `0015_cierres_estado_varchar`) que crea `auditorias` con índices, FK a `usuarios` (ON DELETE SET NULL) y CHECK sobre `accion`/`recurso`.
- Nuevo módulo backend `audit` (`models`, `schemas`, `service`, `masking`, `router`) registrado en `/api/v1/auditoria`.
- Helper `registrar_auditoria(...)` invocado explícitamente desde los servicios de turnos, caja, presupuestos y odontograma, en la misma transacción que la escritura auditada.
- Visor paginado (`GET /api/v1/auditoria`) y export CSV (`GET /api/v1/auditoria/export`), ambos con filtros solo por datos no sensibles.
- Enmascarado centralizado de campos sensibles (salud y PII) aplicado al persistir el `diff` y re-aplicado al exportar (defensa en profundidad).
- RBAC aplicado en backend: solo `admin` consulta y exporta.

## Capabilities

### New Capabilities
- `audit-log`: modelo, migración, helper de registro, enmascarado, visor paginado y export CSV.

### Modified Capabilities
- `core-data-model`: nueva tabla `auditorias` (migración `0016`).
- (Los hooks se describen como requisitos dentro de `audit-log`; no cambian el contrato externo de turnos/caja/presupuestos/odontograma, solo agregan un efecto observable: una fila de auditoría por escritura.)

## Impact

- **Backend / base de datos**: nueva tabla `auditorias` e índices. Requiere `alembic upgrade head`.
- **Código**: nuevo módulo `audit` + llamadas a `registrar_auditoria` en los servicios hookeados + registro del router.
- **Tests**: unitarios de enmascarado y servicio, test de migración `0016`, integración de hooks/RBAC/paginación/export.
- **Dependencias**: C-03, C-12, C-13a, C-16, C-18, C-19 (todas completadas). Sin nuevas dependencias externas.
- **Reglas duras**: R1 (`extra='forbid'`), R2 (sin `tenant_id`), R3/R13 (no se toca append-only ni borrado lógico), R5 (migración + type hints), R8 (RBAC en backend), R9 (sin datos sensibles en logs/URLs), R10 (español rioplatense).
- **Gobernanza**: CRÍTICO. La implementación no se ejecuta sin aprobación humana explícita.