# local-platform Specification

## Purpose
Garantiza un entorno local reproducible y puertas de calidad automáticas para que cada change futuro se verifique igual en cualquier máquina y en CI.

## Requirements

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

El sistema SHALL alinear `backend/pyproject.toml` (`testpaths = ["test"]`,
`pythonpath = ["src"]`, relativos a `backend/`),
`backend/alembic.ini` (`script_location = src/app/db/migrations`, cwd
canónico `backend/`), `env.py` (apunta a `backend/src`, import `app.*`
intacto), `backend/Dockerfile` (contexto `backend/`: `COPY src` +
`uvicorn app.main:app` con `PYTHONPATH=/srv/src`),
`frontend/Dockerfile` (contexto `frontend/`, build vite con `root src`,
nginx desde `/srv/src/dist`), `frontend/package.json` /
`frontend/tsconfig` / `frontend/vite` / `frontend/eslint` (sin prefijos,
cwd `frontend/`), `docker-compose.yml` en raíz (contextos por lado:
`backend`/`frontend` con `dockerfile: Dockerfile`, healthchecks y
`depends_on` intactos), `.env.example` único en raíz, workflow CI (job
backend con `working-directory: backend`: `pytest test`,
`ruff check src test`; job frontend con `working-directory: frontend`:
`tsc`, `eslint src`) y `backend/test/test_structure.py` (aserta
manifiestos en cada lado, ausencia de manifiestos en raíz,
`testpaths = test` y cero `.py` productivos fuera de `backend/src/`) con
el layout canónico KB 08 `backend/{src,test,manifiestos}` +
`frontend/{src,test,manifiestos}`.

#### Scenario: Suite y linters en verde tras el move

- **WHEN** se ejecutan con cwd `backend/` `pytest test -q`,
  `ruff check src test` y `alembic upgrade head`, con cwd `frontend/`
  `tsc --noEmit`, `eslint src` y `npm run build`, y
  `docker compose up --build` + `GET /api/health`
- **THEN** todo pasa/responde `200` sin cambios de comportamiento respecto al
  layout anterior
