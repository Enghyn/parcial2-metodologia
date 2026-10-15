# Spec Delta

## Purpose

Re-mapear el layout backend del contenedor por lado con configs en raíz
(opción 1 de `restructure-por-lado`) al árbol KB 08 literal (opción 2):
manifiestos y configs DENTRO de `backend/`, sin cambiar comportamiento.

## MODIFIED Requirements

### Requirement: Layout raíz src/test única con backend+frontend (§5, sustituye layout por sub-proyecto)

El sistema SHALL ubicar todo el código backend productivo dentro de
`backend/src/` (canónico: `backend/src/app/**`, preservando la raíz de
imports `app.*` vía `pythonpath = ["src"]` en `backend/pyproject.toml`,
relativo a `backend/`) y SHALL ubicar todos los tests backend fuera del
código, en `backend/test/`. Los manifiestos y configs backend SHALL vivir
en `backend/`: `backend/pyproject.toml` (`testpaths = ["test"]`),
`backend/alembic.ini` (`script_location = src/app/db/migrations`, cwd
canónico `backend/`) y `backend/Dockerfile` (nombre canónico KB 08). Las
raíces únicas `src/` y `test/`, y cualquier manifiesto backend en raíz
(`pyproject.toml`, `alembic.ini`, `Dockerfile.backend`), SHALL NOT existir.

#### Scenario: Código contenido en src/backend

- **WHEN** se inspecciona el árbol del repo
- **THEN** todo módulo `.py` de aplicación vive bajo `backend/src/`,
  `backend/pyproject.toml`, `backend/alembic.ini` y `backend/Dockerfile`
  existen en el lado, y ningún `.py` productivo ni manifiesto backend existe
  en raíz

#### Scenario: Tests en raíz test/backend

- **WHEN** se inspecciona el árbol del repo
- **THEN** existe `backend/` en raíz con `backend/src/` (código),
  `backend/test/` (suite: `test_health.py`, `test_settings.py`,
  `test_structure.py`, …) y sus manifiestos propios; NO existe `src/`,
  ni `test/`, ni `src/backend/`, ni `test/backend/`, ni `backend/tests/`
  plural
