# Tasks

## 1. Estructura y backend base

- [x] 1.1 Crear árbol `backend/app/{core,modules/{agenda,lista_espera,clinica,caja,os,notificaciones,admin},adapters,db,workers}` + `frontend/src/{app,features,shared}` y verificar con listado de directorios que existe completo
- [x] 1.2 Implementar `main.py` (app factory), `core/config.py` (pydantic-settings), logger, handler `{error:{code,message,details?}}`, middlewares base y `GET /api/health`, y verificar con `pytest tests/test_health.py` en verde
- [x] 1.3 Inicializar Alembic con migración baseline que habilita `btree_gist` y verificar con `alembic upgrade head` sobre Postgres 15+ limpia

## 2. Frontend base

- [x] 2.1 Scaffold Vite + React 18 + TS estricto + Zustand + Tailwind v4 CSS-first (`@theme`, sin config) y verificar con `tsc --noEmit` en verde
- [x] 2.2 Implementar router `/app/*` privada (redirect a login sin sesión) y `/reservar/*`, `/p/*` públicas, cliente API tipado y contextos auth/tenant, y verificar con build + `eslint` en verde
- [x] 2.3 Aplicar textos públicos en rioplatense y formato ARS, y verificar por inspección de las rutas públicas renderizadas

## 3. Plataforma local y calidad

- [x] 3.1 Escribir `docker-compose.yml` (api + web + postgres 15 + redis 7 + worker) y verificar con `docker compose up` sano + `GET /api/health` → `200`
- [x] 3.2 Crear `.env.example` por sub-proyecto con las 15 variables (`FACTURADOR_MODO=manual`, `ARCA_*` vacías) y verificar que ningún secreto real está commiteado
- [x] 3.3 Agregar workflow CI con jobs paralelos backend (`ruff` + `pytest`) y frontend (`tsc` + `eslint`) y verificar que un push con violación de `ruff` marca el workflow en rojo
- [x] 3.4 Agregar tests de carga de settings y conectividad DB/Redis bajo compose y verificar con la suite fundacional completa en verde

## 4. Enmienda estructural src/test (delta propose, sin tocar código aún — solo fase apply posterior)

- [x] 4.1 Reubicar árbol: `git mv backend/app backend/src/app` y `git mv backend/tests backend/test`, crear `frontend/test/.gitkeep` reservado, y verificar con listado de directorios que `backend/src/app/**` + `backend/test/**` + `frontend/src/**` existen y que NO existe `backend/tests/` ni `.py` productivo fuera de `src/`
- [x] 4.2 Fijar imports/config backend: `pyproject.toml` (`testpaths=["test"]`, `pythonpath=["src"]`), `alembic.ini` (`script_location=src/app/db/migrations`), `env.py` (`sys.path` +1 nivel, `from app.db.base import Base` intacto), revisar `parents[N]` en `test_*.py`/`conftest.py`, y verificar con `pytest backend/test -q` + `ruff check backend/src backend/test` en verde
- [x] 4.3 Fijar Docker/CI/paths: `backend/Dockerfile` (`COPY src` + `PYTHONPATH=/srv/src`, `uvicorn app.main:app`), `ci.yml` (`pytest backend/test`, `ruff check backend/src backend/test`), `tsconfig`/`eslint`/`vite` referenciando `src` (y `frontend/test` solo cuando tenga contenido), `README`/paths en specs, y verificar con `alembic upgrade head` + `docker compose up --build` + `GET /api/health` → `200` y `test_structure` asertando hermanas `src/`/`test/`, `testpaths=test` y cero `.py` fuera de `src/` salvo shims justificados

## 5. Enmienda estructural raíz src/test únicas §5 (delta propose, CORRIGE y SUSTITUYE §4 — sin tocar código aún, solo fase apply posterior)

> Restricción del usuario (vinculante, textual): "esta mal el cambio, lo que queremos es que no haya una carpeta backend y frontend sueltos, con su src y test, queremos un src y un test, ambos con el back y el front". Si alguna skill discrepa (flat-vs-nested), esta restricción gana. Historial 1.1–4.3 intacto arriba.

- [x] 5.1 Reubicar árbol a raíz única: `git mv backend/src/app src/backend/app` y `git mv backend/test test/backend`, `git mv frontend/src/* src/frontend/*` y `frontend/test/.gitkeep` → `test/frontend/.gitkeep`, eliminar las carpetas sueltas `backend/` y `frontend/` como contenedores de código (quedan solo shims movidos a raíz), mover `backend/pyproject.toml` → `pyproject.toml`, `backend/alembic.ini` → `alembic.ini`, `backend/Dockerfile` → `Dockerfile.backend`, `frontend/Dockerfile` → `Dockerfile.frontend`, `frontend/package.json`+`tsconfig`+`vite`+`eslint` → raíz, y verificar con listado de directorios que existen `src/backend/app/**` + `src/frontend/**` + `test/backend/**` + `test/frontend/` y que NO existen `backend/` ni `frontend/` sueltas con código, ni `backend/src`, `backend/test(s)`, `frontend/src`, `frontend/test`
- [x] 5.2 Fijar imports/config: raíz `pyproject.toml` (`testpaths = ["test/backend"]`, `pythonpath = ["src/backend"]`, raíz `app.*` preservada — decisión UNA documentada en `design.md`), `alembic.ini` (`script_location = src/backend/app/db/migrations`), `env.py` (`sys.path` → `src/backend`, `from app.db.base import Base` intacto), `vite.config` (`root = "src/frontend"`), `tsconfig` (`include = ["src/frontend", "test/frontend"]`), `eslint` (`files = ["src/frontend/**", "test/frontend/**"]`), revisar `parents[N]` en `test/backend/*.py`/`conftest.py` por la nueva profundidad, y verificar con `pytest test/backend -q` + `ruff check src/backend test/backend` + `tsc --noEmit` + `eslint src/frontend` en verde
- [x] 5.3 Fijar Docker/CI/paths + verificaciones: `Dockerfile.backend` (`COPY src/backend`, `PYTHONPATH` a `src/backend`, `uvicorn app.main:app`), `Dockerfile.frontend` (`COPY src/frontend`, build con `root src/frontend`), `docker-compose.yml` (contextos raíz), `ci.yml` (`pytest test/backend`, `ruff check src/backend test/backend`, `tsc`/`eslint` sobre `src/frontend`), y verificar con `alembic upgrade head` + `docker compose up --build` + `GET /api/health` → `200` y `test/backend/test_structure.py` asertando hermanas raíz `src/`/`test/` cada una con `backend`+`frontend`, ausencia de `backend/`/`frontend/` sueltas con código, `testpaths = test/backend` y cero `.py` fuera de `src/backend` salvo shims justificados
