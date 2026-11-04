# Sistema Odontológico Multi-Sillón (AR)

Sistema odontológico mono-consultorio con múltiples sillones (2 a 3) para el mercado argentino:
agenda con antisolapamiento, reserva online con link/QR, contacto por WhatsApp, ficha clínica
con odontograma, caja trazable y obras sociales.

## Estado actual

- ✅ `C-01 foundation-setup` archivado (scaffolding + compose + CI).
- ✅ `C-02 core-models-seed` archivado: nueve modelos SQLAlchemy, migración `0002_core_models`
  y seed idempotente, verificados contra PostgreSQL 17.
- ▶ Siguiente: `C-03 auth-jwt-roles` (ver `CHANGES.md`).
- Fuente de verdad del dominio: `knowledge-base/`. Plan de implementación: `CHANGES.md`.
  Reglas del proyecto: `AGENTS.md`.

## Stack

| Capa       | Tecnología                                                        |
|------------|-------------------------------------------------------------------|
| Frontend   | React 18 + TypeScript 5 + Vite + Zustand + Tailwind v4            |
| Backend    | Python 3.12+ + FastAPI + SQLAlchemy + Alembic                     |
| DB / Colas | PostgreSQL 15 (`btree_gist`) / Redis 7 (RQ)                       |
| Infra      | Docker Compose (api + web + postgres + redis + worker), CI GitHub Actions |
| Auth       | JWT Bearer con roles `admin`, `recepcion`, `odontologo` (desde C-03)  |

## Estructura (KB 08 literal — lados autocontenidos)

```text
backend/
  pyproject.toml    # manifiestos + tooling backend (pytest testpaths=test, pythonpath=src)
  alembic.ini       # script_location = src/app/db/migrations (cwd canónico: backend/)
  Dockerfile        # contexto: backend/ (COPY src, PYTHONPATH=/srv/src)
  src/app/**        # todo el código Python (import root: app.*)
  test/             # tests Python (pytest)
frontend/
  package.json      # scripts (lint → eslint src)
  vite.config.ts    # root: "src"
  tsconfig.json     # include: ["src", "test"]
  Dockerfile        # contexto: frontend/ (build vite, nginx desde /srv/src/dist)
  src/**            # todo el código React/TS (entry: src/index.html)
  test/             # tests frontend (cuando haya)
docker-compose.yml  # queda en raíz: orquesta los cinco servicios (contextos por lado)
.env.example        # queda en raíz: plantilla única (cp .env.example .env)
```

Cada lado se opera desde su propio cwd (`backend/`, `frontend/`). Nada de código
vive en raíz: solo orquestación (`docker-compose.yml`), plantilla de entorno
(`.env.example`), CI (`.github/`), docs y tooling a nivel repo.

## Quickstart

```bash
# 1. Variables de entorno (sin secretos hardcodeados)
cp .env.example .env

# 2. Levantar todo
docker compose up --build

# 3. Verificar
curl http://localhost:8000/api/health   # → {"status":"ok"}
# Web en http://localhost:5173
```

Desarrollo local (sin Docker):

```bash
# Backend (cwd backend/)
cd backend
pip install -e ".[dev]"
pytest test -q
ruff check src test

# Frontend (cwd frontend/)
cd frontend
npm ci
npm run dev     # Vite
npm run build   # tsc + build
npm run lint    # eslint src
```

## Después de un `git pull`

El pull trae código y specs, pero **no toca tu PostgreSQL**. Antes de levantar el backend o correr tests de integración:

```bash
cd backend
pip install -e ".[dev]"   # solo si cambiaron dependencias
alembic upgrade head
python -m app.db.seed     # opcional: datos de demo, idempotente
pytest -m "not integration" -q   # rápido, sin base
pytest -q                        # completo, con base
```

Si falla la conexión, revisá `DATABASE_URL` y que PostgreSQL esté corriendo. No corras `alembic -c backend/alembic.ini` desde la raíz: el cwd canónico es `backend/`.

Migraciones (cwd canónico `backend/`):

```bash
cd backend
alembic upgrade head
```

Datos de demostración (idempotente; no corre al arrancar la app):

```bash
cd backend
python -m app.db.seed --help
python -m app.db.seed
```

Crea 3 sillones, 4 usuarios (1 admin, 1 recepción, 2 odontólogos), 2 profesionales y 2 pacientes.
Credenciales de demo: `admin@consultorio.com` / `admin123`, `recepcion@consultorio.com` /
`recepcion123`, `dr.perez@consultorio.com` y `dra.gomez@consultorio.com` / `odontologo123`.
Se puede forzar otra contraseña con `SEED_DEFAULT_PASSWORD`; el seed se bloquea con
`APP_ENV=production` salvo `--force`.

## Variables de entorno

Ver `.env.example` (15 variables): `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `WA_*`,
`MP_*`, `FACTURADOR_MODO=manual`, `ARCA_*` (vacías hasta fase 2), `CORS_ORIGINS`.
Nunca commitear un `.env` real (ver `.gitignore`).

## Calidad

| Chequeo | Comando (cwd canónico)              |
|---------|---------------------------------------|
| Backend unit | `pytest -m "not integration" -q` (cwd `backend/`, sin base) |
| Backend integración | `pytest -q` (cwd `backend/`, requiere `alembic upgrade head` + seed) |
| Backend lint  | `ruff check src test` (cwd `backend/`) |
| Frontend tipos | `npx tsc --noEmit` (cwd `frontend/`) |
| Frontend lint | `npm run lint` (cwd `frontend/`)  |
| Todo (CI) | jobs paralelos backend + frontend con `working-directory` por lado (`.github/workflows/`) |

## Documentación

- `knowledge-base/` — dominio (leer el archivo relevante antes de implementar).
- `docs/discovery/` — discovery de mercado y competidores.
- `CHANGES.md` — roadmap de 8 changes académicos (C-01 a C-08).
- `openspec/specs/` — especificaciones sincronizadas (fuente de verdad técnica).
- `AGENTS.md` / `CLAUDE.md` — instrucciones y reglas duras para agentes.
