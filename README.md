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

## Estructura (decisión §5 — única raíz `src/` y `test/`)

```text
src/
  backend/      # todo el código Python (import root: app.*)
  frontend/     # todo el código React/TS
test/
  backend/      # tests Python (pytest)
  frontend/     # tests frontend (cuando haya)
```

No existen carpetas `backend/` ni `frontend/` sueltas: todo el código vive bajo `src/`,
todos los tests bajo `test/`. Configs y shims quedan en raíz (`pyproject.toml`,
`package.json`, `vite.config.ts`, `alembic.ini`, `Dockerfile.backend`, `Dockerfile.frontend`).

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
# Backend (desde la raíz)
pip install -e ".[dev]"
pytest test/backend -q
ruff check src/backend test/backend

# Frontend (desde la raíz)
npm install
npm run dev     # Vite
npm run build   # tsc + build
npm run lint    # eslint
```

Migraciones:

```bash
alembic upgrade head
```

## Variables de entorno

Ver `.env.example` (15 variables): `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `WA_*`,
`MP_*`, `FACTURADOR_MODO=manual`, `ARCA_*` (vacías hasta fase 2), `CORS_ORIGINS`.
Nunca commitear un `.env` real (ver `.gitignore`).

## Calidad

| Chequeo | Comando (desde raíz)              |
|---------|-----------------------------------|
| Backend tests | `pytest test/backend -q`    |
| Backend lint  | `ruff check src/backend test/backend` |
| Frontend tipos | `tsc --noEmit`               |
| Frontend lint | `npm run lint`                |
| Todo (CI) | jobs paralelos backend + frontend (`.github/workflows/`) |

## Documentación

- `knowledge-base/` — dominio (leer el archivo relevante antes de implementar).
- `docs/discovery/` — discovery de mercado y competidores.
- `CHANGES.md` — roadmap de 22 changes en 5 fases + cobertura del MVP (C-01–C-17).
- `openspec/specs/` — especificaciones sincronizadas (fuente de verdad técnica).
- `AGENTS.md` / `CLAUDE.md` — instrucciones y reglas duras para agentes.
