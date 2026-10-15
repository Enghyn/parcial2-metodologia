# Spec Delta

## Purpose

Realinear tooling y configuración al árbol KB 08 literal (opción 2):
cada lado con sus manifiestos, compose en raíz con contextos por lado, CI
con `working-directory` por lado y `.env.example` único en raíz, sin
cambiar servicios, puertas ni comportamiento.

## MODIFIED Requirements

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
