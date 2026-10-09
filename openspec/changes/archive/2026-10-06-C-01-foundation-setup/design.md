# Design

## Context

Ver `proposal.md` (Why). Estado actual: repo sin código; solo KB, `CHANGES.md`, skills y registry. Restricciones: DD-01 (monolito modular, un Compose), DD-02 (Python 3.12, FastAPI, SQLAlchemy 2.0, Postgres 15+, Redis 7+), DD-03 (SPA React 18 + TS + Vite; SEO avanzado a fase 2). Reglas duras R1, R5, R7, R9, R10, R11, R12 aplican desde este change.

## Goals / Non-Goals

**Goals:**

- Esqueleto que compila, levanta en compose y pasa CI en verde, listo para recibir modelos de C-02.
- Decisiones irreversibles tomadas ahora: layout de módulos, forma de error, estrategia de settings, baseline Alembic con `btree_gist`, superficies del router.

**Non-Goals:**

- Ninguna tabla de dominio, endpoint de negocio, auth real ni RBAC (C-02/C-03).
- Ninguna integración real WA/MP/ARCA: SDK instalado, adapters vacíos con interfaz declarada como muy tarde en sus changes (C-07/C-11/C-16).
- Optimización de performance, RLS (deuda declarada hasta fase 2), multi-sede, SEO avanzado.

## Decisions

- **Layout backend `app/{api/v1/endpoints, core, models, schemas, services, repositories} + main.py` dentro de `modules/` por dominio** (fastapi-templates): routers versionados `/api/v1`; handlers `async`; sesiones vía `get_db` con `Depends`; schemas Pydantic separados input/output con `extra="forbid"` (R1). Alternativa (flat por capa sin `modules/`) descartada: DD-01 exige fronteras de módulo para agenda/clínica/caja.
- **Error único `{error:{code,message,details?}}` + mapa 400/401/403/404/409/422/500** (api-and-interface-design): se fija en C-01 para que ningún change posterior invente su formato. Campos de respuesta en `camelCase`; listas futuras siempre paginadas.
- **`BIGINT GENERATED ALWAYS AS IDENTITY`, `TIMESTAMPTZ`, `NUMERIC` para dinero, `TEXT`, `snake_case` sin comillas, índice manual por FK** (postgresql-table-design); `btree_gist` habilitado en baseline para el `EXCLUDE` de C-05 (R6). Sin RLS en v1: filtro `tenant_id` en sesión, deuda declarada (supabase-postgres-best-practices como mindset, no enforcement aún).
- **Workers Redis (RQ) desde C-01 con una tarea `ping`**: deja el cableado `api → redis → worker` verificado antes de los recordatorios de C-07 (async-python-patterns: lo asíncrono real vive en workers, nunca en handlers).
- **Tailwind v4 CSS-first** (`@import "tailwindcss"` + `@theme`, sin config; tokens OKLCH; base `border-border` / `bg-background`) y **TS estricto sin `any`, componentes `PascalCase`** (R7). Superficies públicas en rioplatense, ARS (R10). Sin barrel imports; `Promise.all` para fetches paralelos futuros.
- **CI mínimo bloqueante**: `ruff + pytest` y `tsc --noEmit + eslint` en jobs paralelos. Sin cobertura mínima exigible todavía (se fija en C-02 con lógica real que testear).
- **Layout canónico RAÍZ `src/` + `test/` únicas, cada una con `backend`+`frontend` (restricción del usuario §5, CORRIGE y SUSTITUYE la decisión §4 de `src/`/`test/` por sub-proyecto; el usuario prevalece sobre cualquier default de skill)**: todo el código productivo vive DENTRO de raíz `src/` — `src/backend/app/**` (todo el Python/FastAPI) + `src/frontend/**` (`{app,features,shared}` + `main.tsx`, `index.css`, `vite-env.d.ts`); todos los tests viven FUERA, en raíz `test/` — `test/backend/**` (suite pytest) + `test/frontend/**` (futura suite frontend, `.gitkeep` si vacía). Las carpetas sueltas `backend/` y `frontend/` como contenedores de código QUEDAN ELIMINADAS: no existen como hermanas con su propio `src`/`test`. (a) Import root `app.*` PRESERVADO: `pythonpath = ["src/backend"]` (única raíz Python), de modo que `from app.main import create_app`, `uvicorn app.main:app` y `sys.path` en `env.py` siguen válidos; la alternativa `PYTHONPATH=raíz/src` obligaría a reescribir cada import a `backend.app.*` y rompería el patrón `fastapi-templates` (`app/main.py` como entry) — DESCARTADA explícitamente, un solo `pythonpath` ganado. (b) La frontera back/front baja UN nivel (`src/backend` vs `src/frontend`): `docker-compose` construye `api` y `web` con `COPY src/backend` / `COPY src/frontend` por separado y CI corre `ruff src/backend test/backend` + `pytest test/backend` vs `tsc`/`eslint` sobre `src/frontend` — contextos de build y jobs intactos, sin mezcla. (c) `test/` singular en raíz por mandato literal ("un src y un test"); `backend/tests/`, `backend/test/`, `frontend/test/` y `backend/`, `frontend/` sueltas como contenedores quedan prohibidas.
- **Shims/configs que quedan FUERA de `src/` (todos en raíz, con justificación explícita)**: `pyproject.toml` (raíz: declara `testpaths = ["test/backend"]` + `pythonpath = ["src/backend"]`; es manifiesto de build, las herramientas lo resuelven desde el cwd del repo); `package.json` (raíz: `workdir` único de `npm`, scripts `tsc`/`eslint`/`vite` con rutas a `src/frontend`); `vite.config.ts` (`root: "src/frontend"`); `tsconfig*.json` (`include: ["src/frontend", "test/frontend"]`); `eslint.config.*` (`files: ["src/frontend/**", "test/frontend/**"]`); `alembic.ini` (raíz: `script_location = src/backend/app/db/migrations`); `Dockerfile.backend` / `Dockerfile.frontend` (raíz: contextos `COPY src/backend` / `COPY src/frontend`); `docker-compose.yml`, `.env.example`, `.github/workflows/ci.yml` (orquestación y puertas de calidad, nunca código importable). Ningún `.py`/`.tsx` productivo fuera de `src/`; ningún test fuera de `test/`.

## Risks / Trade-offs

- [Render blocking] `mercadopago-sdk` instalado sin uso hasta C-16 → se fija versión exacta en `pyproject.toml` para evitar drift.
- [Exclusión] `btree_gist` en baseline exige Postgres 15+ real en compose y CI → imagen pineada `postgres:15` y test de conectividad que falla si falta la extensión.
- [Deuda] Sin RLS el aislamiento depende de disciplina `tenant_id` (R2) → C-02 agrega `BaseRepository` + test de aislamiento que lo hace exigible.
- [Deuda] `ARCA_*` vacías y `FACTURADOR_MODO=manual` → el adapter real llega en C-11/C-21 sin tocar caja (DD-05).

## Migration Plan

No hay despliegue previo: primer `docker compose up --build` + `alembic upgrade head`. Rollback = borrar volúmenes y contenedores (`docker compose down -v`). Sin datos que migrar.

### Mapa de reubicación old → new §5 (CORRIGE y SUSTITUYE el mapa §4; solo fase apply; esta propuesta solo edita artefactos)

| Antes (working tree actual) | Después (canónico §5) | Notas |
|---|---|---|
| `backend/src/app/**` | `src/backend/app/**` | `git mv` del árbol completo; imports `app.*` intactos con `pythonpath = ["src/backend"]` |
| `backend/test/**` | `test/backend/**` | `git mv`; `testpaths = ["test/backend"]`; revisar `parents[N]` en `test_*.py`/`conftest.py` por nueva profundidad |
| `frontend/src/**` | `src/frontend/**` | `git mv` (`app/`, `features/`, `shared/`, `main.tsx`, `index.css`, `vite-env.d.ts`); `vite.config root = "src/frontend"`, `tsconfig include = ["src/frontend", "test/frontend"]` |
| `frontend/test/.gitkeep` | `test/frontend/.gitkeep` | Única ubicación futura de tests frontend; `eslint files = ["src/frontend/**", "test/frontend/**"]` |
| `backend/pyproject.toml` | `pyproject.toml` (raíz, editado) | `testpaths = ["test/backend"]` + `[tool.pytest.ini_options] pythonpath = ["src/backend"]`; manifiesto de build, vive en raíz |
| `backend/alembic.ini` | `alembic.ini` (raíz, editado) | `script_location = src/backend/app/db/migrations` |
| `src/backend/app/db/migrations/env.py` | `sys.path` base ajustada | Apunta a `src/backend`; import `from app.db.base import Base` sin cambios |
| `backend/Dockerfile` | `Dockerfile.backend` (raíz, editado) | `COPY src/backend ./src/backend` (o `COPY src/backend/ /srv/src/backend/`); `CMD ["uvicorn", "app.main:app", ...]` con `PYTHONPATH=/srv/src/backend` |
| `frontend/Dockerfile` (o build web) | `Dockerfile.frontend` (raíz, editado) | `COPY src/frontend` + build vite con `root src/frontend` |
| `frontend/package.json`, `tsconfig*.json`, `vite.config.ts`, `eslint.config.*` | raíz (editados) | Rutas a `src/frontend` (+ `test/frontend` donde aplique); `workdir` único en raíz |
| `.github/workflows/ci.yml`, `docker-compose.yml`, `.env.example` | raíz (editados) | `pytest test/backend -q`, `ruff check src/backend test/backend`, `tsc/eslint` sobre `src/frontend`; compose con contextos raíz |
| `test_structure.py` | `test/backend/test_structure.py` (editado) | Aserta: existen `src/` y `test/` hermanas en raíz, cada una con `backend`+`frontend`; NO existen carpetas sueltas `backend/` ni `frontend/` con código; `testpaths = test/backend`; ningún `.py` productivo fuera de `src/backend` salvo shims de config justificados (`pyproject.toml`, `alembic.ini`, `conftest.py` bajo `test/`) |

Excepciones justificadas fuera de `src/`: solo shims de configuración en raíz (`pyproject.toml`, `package.json`, `vite.config.ts`, `tsconfig*.json`, `eslint.config.*`, `alembic.ini`, `Dockerfile.backend`, `Dockerfile.frontend`, `docker-compose.yml`, `.env.example`, `.github/workflows/ci.yml`) y `conftest.py`/tests bajo `test/`. Ningún `.py` de aplicación fuera de `src/backend`; ningún `.tsx/.ts/.css` productivo fuera de `src/frontend`; ningún test fuera de `test/`.

## Open Questions

Ninguna que cambie specs, enfoque o tasks: las preguntas abiertas de prioridad alta de `10_preguntas_abiertas.md` (exportación CSV, seña, login público) pertenecen a sus changes (C-04/C-14/C-16/C-17), no al scaffolding.
