# backend-foundation Specification

## Purpose
Define el contrato operativo mínimo del backend FastAPI sobre el que corre todo el MVP: arranque, salud, configuración, errores y migraciones.

## Requirements

### Requirement: Health check versionado

El sistema SHALL exponer `GET /api/health` que responde `200` con el estado de la aplicación sin requerir autenticación.

#### Scenario: Health responde OK

- **WHEN** un cliente hace `GET /api/health`
- **THEN** responde `200` con `{status: "ok"}` y sin exigir token

### Requirement: Configuración por entorno con validación estricta

El sistema SHALL cargar toda su configuración desde variables de entorno mediante `pydantic-settings`, fallando al arrancar si falta una variable requerida, y SHALL rechazar campos no declarados en todo schema Pydantic con `extra="forbid"`.

#### Scenario: Falta variable requerida

- **WHEN** se arranca la API sin `DATABASE_URL`
- **THEN** el arranque falla con un error que nombra la variable faltante

#### Scenario: Payload con campo desconocido

- **WHEN** un request trae un campo no declarado en el schema
- **THEN** la API responde `422` con forma de error única

### Requirement: Forma única de error

El sistema SHALL responder todos los errores con la forma `{error: {code, message, details?}}` y el mapa de estados `400/401/403/404/409/422/500`, sin exponer detalles internos en `500`.

#### Scenario: Error interno

- **WHEN** ocurre una excepción no manejada
- **THEN** responde `500` con `code` genérico y sin stack trace ni DSN

### Requirement: Logging sin datos de salud

El sistema SHALL emitir logs estructurados que nunca incluyen datos de salud del paciente (solo identificadores operativos como día, hora o profesional cuando aplique).

#### Scenario: Request con datos clínicos

- **WHEN** se procesa un payload con información de salud
- **THEN** ningún log emitido contiene ese contenido clínico

### Requirement: Baseline Alembic con btree_gist

El sistema SHALL proveer Alembic inicializado con una migración baseline vacía que habilita la extensión Postgres `btree_gist`, lista para recibir los modelos multi-tenant de C-02.

#### Scenario: Migración baseline

- **WHEN** se ejecuta `alembic upgrade head` sobre una base Postgres 15+ limpia
- **THEN** la extensión `btree_gist` queda disponible y no existe aún ninguna tabla de dominio

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
