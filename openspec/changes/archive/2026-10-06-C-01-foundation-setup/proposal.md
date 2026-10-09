# Proposal

## Why

No existe código todavía: sin una base componible (backend, frontend, compose, CI) ningún change del camino crítico (C-02 → C-17) puede implementarse ni verificarse. Este change crea el esqueleto del monolito modular sobre el que corre todo el MVP, sin lógica de dominio.

## What Changes

- Estructura `backend/src/app/{core,modules/{agenda,lista_espera,clinica,caja,os,notificaciones,admin},adapters,db,workers}` y `frontend/src/{app,features,shared}` según `08_arquitectura_propuesta.md` §Estructura. **Todo el código vive dentro de `src/`**; los tests viven fuera, en una carpeta `test/` hermana al mismo nivel que `src/` (restricción estructural del usuario).
- Backend FastAPI mínimo con `GET /api/health`, settings por `pydantic-settings`, logger estructurado, handler de errores único y middlewares base; Alembic inicializado con baseline vacío.
- Frontend Vite + React 18 + TS estricto + Zustand + Tailwind v4 con router: superficie privada `/app/*` y superficies públicas `/reservar/*`, `/p/*`.
- `docker-compose.yml` con `api` + `web` + `postgres:15+` (extensión `btree_gist` habilitada) + `redis:7+` + `worker`.
- `.env.example` por sub-proyecto con las 15 variables de §Variables (`DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `JWT_EXPIRE_MIN`, `WA_TOKEN`, `WA_PHONE_ID`, `WA_WEBHOOK_VERIFY`, `MP_ACCESS_TOKEN`, `MP_WEBHOOK_SECRET`, `TENANT_DEFAULT_CANCEL_HS`, `LISTA_ESPERA_OFERTA_MIN`, `FACTURADOR_MODO=manual`, `ARCA_*` vacías, `CORS_ORIGINS`); cero secretos hardcodeados.
- CI en GitHub Actions con jobs paralelos: backend (`ruff` + `pytest`) y frontend (`tsc --noEmit` + `eslint`).
- Tests fundacionales: health check 200, carga de settings desde entorno, conectividad Postgres/Redis bajo compose.
- **Enmienda de layout (sin cambio de comportamiento)**: el código backend implementado en `backend/app/` se reubica bajo `backend/src/app/` y los tests de `backend/tests/` a `backend/test/` (singular); `frontend/src/` se mantiene y `frontend/test/` queda reservado como único lugar para futuros tests frontend. Se actualizan en consecuencia import paths, `pyproject.toml` (`testpaths`, `pythonpath`), `tsconfig`/`vite`/`eslint`, Dockerfiles (`COPY src`), workflow CI, `alembic.ini` + `env.py` y los pasos de verificación de `tasks.md`. Decisión explícita: `src/` por sub-proyecto (`backend/src/`, `frontend/src/`), NO un único `src/` en raíz, porque `docker-compose` construye `api` y `web` por separado y CI corre `ruff`/`pytest` vs `tsc`/`eslint` por job — un `src/` raíz rompería esas fronteras.
- **Enmienda §5 — CORRIGE y SUSTITUYE la decisión de layout de §4 (restricción del usuario, vinculante, prevalece sobre cualquier default de skill)**. Cita textual del usuario: "esta mal el cambio, lo que queremos es que no haya una carpeta backend y frontend sueltos, con su src y test, queremos un src y un test, ambos con el back y el front". Canónico nuevo: RAÍZ `src/` única con `src/backend/**` (todo el Python/FastAPI, ex `backend/src/app/**`) + `src/frontend/**` (todo el Vite/React, ex `frontend/src/**`); RAÍZ `test/` única con `test/backend/**` (ex `backend/test/**`) + `test/frontend/**` (ex ubicación frontend; se crea con `.gitkeep` si está vacía). Se ELIMINAN las carpetas sueltas `backend/` y `frontend/` como contenedores de código: no deben quedar como hermanas cada una con su propio `src`/`test`. Por qué raíz `src/`+`test/`: un solo árbol de código y un solo árbol de tests simplifican onboarding, búsquedas, linters y CI (un `pytest test/backend`, un `tsc` sobre `src/frontend`), sin mezclar contextos porque la frontera back/front vive UN nivel más abajo (`src/backend` vs `src/frontend`). Import root `app.*` preservado vía `pythonpath = ["src/backend"]` (decisión documentada en `design.md`). Configs/shims que quedan FUERA de `src/` (raíz): `pyproject.toml`, `package.json`, `vite.config.ts`, `tsconfig*.json`, `eslint.config.*`, `alembic.ini`, `Dockerfile.backend`, `Dockerfile.frontend`, `docker-compose.yml`, `.env.example`, `.github/workflows/ci.yml` — justificación por archivo en `design.md`.

## Capabilities

### New Capabilities

- `backend-foundation`: contrato operativo del backend — app factory, `GET /api/health`, configuración por entorno, logging sin PHI, forma única de error, middlewares base y baseline Alembic con `btree_gist`.
- `frontend-foundation`: cascarón de la SPA — superficies privada y públicas, tema Tailwind v4, cliente API tipado, contextos de auth/tenant y convenciones rioplatense + ARS.
- `local-platform`: entorno local reproducible y puertas de calidad — servicios compose, `.env.example` completos, CI paralelo y tests de conectividad.

### Modified Capabilities

(none — repo sin specs previas; `openspec/specs/` solo contiene `.gitkeep`)

## Impact

- Archivos nuevos: `backend/`, `frontend/`, `docker-compose.yml`, `.github/workflows/ci.yml`, `.env.example`(s). No se toca código de dominio porque no existe.
- **Enmienda sin comportamiento**: reubica `backend/app/**` → `backend/src/app/**` y `backend/tests/**` → `backend/test/**`; `frontend/src/**` intacto, `frontend/test/` reservado. Actualiza `pyproject.toml`, `alembic.ini`, `Dockerfile`s, `ci.yml`, `tsconfig`/`eslint` y `test_structure.py`. Sin cambio de APIs, contratos ni dependencias.
- **Enmienda §5 (sustituye a la anterior)**: reubica `backend/src/app/**` → `src/backend/app/**`, `backend/test/**` → `test/backend/**`, `frontend/src/**` → `src/frontend/**`, `frontend/test/` → `test/frontend/`; elimina las carpetas sueltas `backend/` y `frontend/` como contenedores de código; mueve configs a raíz (`pyproject.toml` con `testpaths = ["test/backend"]` + `pythonpath = ["src/backend"]`, `alembic.ini` con `script_location = src/backend/app/db/migrations`, `package.json`/`tsconfig`/`vite`/`eslint` sobre `src/frontend`, Dockerfiles con `COPY src/backend` / `COPY src/frontend`, CI con `pytest test/backend` + `ruff src/backend test/backend`); `test_structure` aserta hermanas raíz `src/`/`test/` cada una con `backend`+`frontend`, ausencia de carpetas sueltas con código y cero `.py` fuera de `src/backend` salvo shims justificados. Sin cambio de APIs, contratos ni dependencias.
- Dependencias externas nuevas: imágenes `postgres:15+`, `redis:7+`; paquetes `fastapi`, `sqlalchemy`, `alembic`, `pydantic-settings`, `redis`/`rq`, `mercadopago-sdk` (instalado, sin uso hasta C-16).
- Desbloquea C-02 (`core-models-tenancy`): migraciones, modelos y seed corren sobre esta base. Sin impacto en producción (no hay deploy previo).
