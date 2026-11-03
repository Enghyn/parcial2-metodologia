# Proposal — C-02b core-data-model-hardening

## Why

La auditoría de reglas sobre C-02 encontró tres brechas entre la spec archivada y el código, y dos reglas duras (R3 y R13) que hoy solo se sostienen en el ORM: un `UPDATE`/`DELETE` por SQL crudo puede evadirlas. Antes de construir C-03 (login por email) y C-04 (agenda), el contrato de datos tiene que quedar consistente; si no, esos changes heredan las mismas ambigüedades.

## What Changes

- **Email normalizado y case-insensitive**: `Usuario` normaliza `email` con `trim + lower` y la base exige `email = lower(btrim(email))`; el duplicado se rechaza ignorando mayúsculas (hoy el único es case-sensitive).
- **Motivo de bloqueo no vacío**: `bloqueos.motivo` deja de aceptar `""` o solo espacios mediante `CHECK`.
- **Coherencia `fin`/`duracion_min`**: `turnos` exige `fin = inicio + duracion_min * interval '1 minute'`, cerrando RN-AG-02 a nivel de datos.
- **Defensa en base para R3 y R13**: triggers `BEFORE UPDATE OR DELETE` en `movimientos_caja` y `BEFORE DELETE` en `pacientes`, `turnos`, `profesionales` y `sillones`. Las guardas ORM se mantienen para dar errores amigables; los triggers cubren SQL crudo.
- **Aclaración de spec**: el nombre del profesional es obligatorio pero **no único**; la matrícula sí es única.
- **Seed robusto**: si no hay base, el comando falla con mensaje operativo claro, hace rollback y devuelve código distinto de cero.
- **Tests faltantes**: cobertura completa de RN-CJ-01 (fecha, medio, concepto, usuario), normalización de email, motivo vacío, `fin` incoherente y guardas en PostgreSQL real.
- **Handoff documentado**: criterio `deleted_at IS NULL` para C-04/C-07/C-08 y preguntas abiertas (duración por prestación, momento de deducción de la seña) en `knowledge-base/10_preguntas_abiertas.md`.

**BREAKING (solo datos de desarrollo):** las nuevas constraints rechazan filas existentes con email sin normalizar, `motivo` vacío o `fin` incoherente. El seed actual no genera esos casos.

## Capabilities

### New Capabilities

- Ninguna.

### Modified Capabilities

- `core-data-model`: se refuerzan identidad de usuarios, profesionales, integridad temporal de turnos, bloqueos, inmutabilidad de caja y borrado lógico.

## Impact

- **Modelos**: `backend/src/app/modules/admin/models.py`, `backend/src/app/modules/agenda/models.py`.
- **Migración**: nueva `backend/src/app/db/migrations/versions/0003_core_data_model_hardening.py` (constraints + funciones/triggers), con downgrade completo.
- **Seed**: `backend/src/app/db/seed.py` (manejo de error de conexión y rollback).
- **Tests**: `test_models_structure.py`, `test_migration_0003.py`, `test_seed.py`, `test_caja_inmutable.py` y un test de integración opcional con PostgreSQL.
- **Docs**: `CHANGES.md` (criterios para C-04/C-07/C-08) y `knowledge-base/10_preguntas_abiertas.md`.
- **Sin cambios** de API, frontend ni dependencias nuevas.
