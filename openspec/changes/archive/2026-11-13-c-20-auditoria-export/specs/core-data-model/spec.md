# Spec Delta

## ADDED Requirements

### Requirement: Tabla auditorias (migración 0016)

El sistema SHALL crear mediante la migración `0016_auditoria` (encadenada a `0015_cierres_estado_varchar`, reversible con `downgrade`) la tabla `auditorias`, sin `tenant_id` (R2), con las columnas e índices definidos en la capability `audit-log`, y un CHECK `accion` sobre el catálogo controlado y un CHECK `recurso` sobre el catálogo controlado.

#### Scenario: Upgrade crea la tabla
- **WHEN** se ejecuta `alembic upgrade head` sobre una base con `0015_cierres_estado_varchar` aplicada
- **THEN** existe `auditorias` con sus índices y constraints, y `estado_cierre` sigue ausente de `pg_type`

#### Scenario: Downgrade sin objetos huérfanos
- **WHEN** se ejecuta `alembic downgrade` hasta `0015_cierres_estado_varchar`
- **THEN** `auditorias` no existe y no quedan índices ni constraints huérfanos