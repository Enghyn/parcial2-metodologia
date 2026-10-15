# Sistema Odontológico Multi-Sillón (AR)

SaaS multi-tenant para consultorios y clínicas odontológicas argentinas: agenda multi-sillón
con antisolapamiento, reserva online 24/7 con link/QR, recordatorios por WhatsApp, ficha clínica
con odontograma, caja trazable + Mercado Pago, obras sociales y reportes.

## Estado actual

- ✅ `C-01 foundation-setup` archivado (scaffolding + compose + CI).
- ▶ Siguiente: `C-02 core-models-tenancy` (ver `CHANGES.md`, GATE 1).
- Fuente de verdad del dominio: `knowledge-base/`. Plan de implementación: `CHANGES.md`.
  Reglas del proyecto: `AGENTS.md`.

## Stack

| Capa       | Tecnología                                                        |
|------------|-------------------------------------------------------------------|
| Frontend   | React 18 + TypeScript 5 + Vite + Zustand + Tailwind v4            |
| Backend    | Python 3.12+ + FastAPI + SQLAlchemy + Alembic                     |
| DB / Colas | PostgreSQL 15 (`btree_gist`) / Redis 7 (RQ)                       |
| Infra      | Docker Compose (api + web + postgres + redis + worker), CI GitHub Actions |
| Auth       | JWT access corto + refresh rotado, claim `tenant_id` (desde C-03)  |

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

Migraciones (cwd canónico `backend/` — prohibido `alembic -c backend/alembic.ini`
desde raíz):

```bash
cd backend
alembic upgrade head
```

## Variables de entorno

Ver `.env.example` (15 variables): `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `WA_*`,
`MP_*`, `FACTURADOR_MODO=manual`, `ARCA_*` (vacías hasta fase 2), `CORS_ORIGINS`.
Nunca commitear un `.env` real (ver `.gitignore`).

## Calidad

| Chequeo | Comando (cwd canónico)              |
|---------|---------------------------------------|
| Backend tests | `pytest test -q` (cwd `backend/`) |
| Backend lint  | `ruff check src test` (cwd `backend/`) |
| Frontend tipos | `npx tsc --noEmit` (cwd `frontend/`) |
| Frontend lint | `npm run lint` (cwd `frontend/`)  |
| Todo (CI) | jobs paralelos backend + frontend con `working-directory` por lado (`.github/workflows/`) |

## Documentación

- `knowledge-base/` — dominio (leer el archivo relevante antes de implementar).
- `docs/discovery/` — discovery de mercado y competidores.
- `CHANGES.md` — roadmap de 22 changes en 5 fases + cobertura del MVP (C-01–C-17).
- `openspec/specs/` — especificaciones sincronizadas (fuente de verdad técnica).
- `AGENTS.md` / `CLAUDE.md` — instrucciones y reglas duras para agentes.
