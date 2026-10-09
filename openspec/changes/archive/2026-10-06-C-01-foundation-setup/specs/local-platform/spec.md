# Spec Delta

## Purpose

Garantiza un entorno local reproducible y puertas de calidad automáticas para que cada change futuro se verifique igual en cualquier máquina y en CI.

## ADDED Requirements

### Requirement: Compose con cinco servicios

El sistema SHALL proveer un `docker-compose.yml` que levanta `api`, `web`, `postgres:15+` con `btree_gist` habilitado, `redis:7+` y `worker`, donde `api` responde `GET /api/health` con `200`.

#### Scenario: Levantar el entorno

- **WHEN** se ejecuta `docker compose up` con el `.env` de ejemplo
- **THEN** los cinco servicios quedan sanos y `GET /api/health` responde `200`

### Requirement: Variables de entorno documentadas sin secretos

El sistema SHALL incluir `.env.example` por sub-proyecto con las 15 variables de `08_arquitectura_propuesta.md` §Variables (`FACTURADOR_MODO=manual`, `ARCA_*` vacías en fase 1) y SHALL NOT contener ningún secreto hardcodeado en el repo.

#### Scenario: Auditoría de secretos

- **WHEN** se inspecciona el repo
- **THEN** toda variable sensible tiene placeholder en `.env.example` y ningún valor real aparece commiteado

### Requirement: CI con jobs paralelos

El sistema SHALL ejecutar en CI dos jobs paralelos: backend (`ruff` + `pytest`) y frontend (`tsc --noEmit` + `eslint`), bloqueando el merge si alguno falla.

#### Scenario: Push con error de lint

- **WHEN** un push introduce una violación de `ruff`
- **THEN** el job backend falla y el workflow completo se marca en rojo

### Requirement: Tests fundacionales

El sistema SHALL incluir tests que verifican el health check, la carga de settings desde entorno y la conectividad a Postgres y Redis bajo compose.

#### Scenario: Suite fundacional en verde

- **WHEN** se corre la suite sobre el entorno compose
- **THEN** los tests de health, settings y conectividad DB/Redis pasan

### Requirement: Configuración y tooling alineados al layout raíz src/test (§5)

El sistema SHALL alinear `pyproject.toml` en raíz (`testpaths = ["test/backend"]`, `pythonpath = ["src/backend"]`), `alembic.ini` en raíz (`script_location = src/backend/app/db/migrations`), `env.py` (apunta a `src/backend`, import `app.*` intacto), `Dockerfile.backend` (`COPY src/backend` + `uvicorn app.main:app` con `PYTHONPATH` a `src/backend`), `Dockerfile.frontend` (`COPY src/frontend`, build vite con `root src/frontend`), `package.json`/`tsconfig`/`vite`/`eslint` en raíz sobre `src/frontend` (+ `test/frontend`), workflow CI (`pytest test/backend`, `ruff check src/backend test/backend`) y `test/backend/test_structure.py` (aserta hermanas raíz `src/`/`test/` cada una con `backend`+`frontend`, ausencia de carpetas sueltas `backend/`/`frontend/` con código, `testpaths = test/backend` y cero `.py` productivos fuera de `src/backend/`) con el layout canónico `src/backend/app/**` + `test/backend/**` + `src/frontend/**` + `test/frontend/`.

#### Scenario: Suite y linters en verde tras el move

- **WHEN** se ejecutan `pytest test/backend -q`, `ruff check src/backend test/backend`, `alembic upgrade head` y `docker compose up --build` + `GET /api/health`
- **THEN** todo pasa/responde `200` sin cambios de comportamiento respecto al layout anterior
