# Tasks — mudanza-completa-configs

> Governance LOW: mudanza mecánica de configs + re-apuntes + docs. Solo
> artefactos acá; la ejecución la hace `/opsx:apply`. Verificaciones
> ejecutables por task (R11: sin commit). Tras cada grupo, suite en verde.

## 1. Moves con git mv + renombres canónicos (cero ediciones de contenido)

- [x] 1.1 Mover con `git mv`: `pyproject.toml → backend/pyproject.toml`,
  `alembic.ini → backend/alembic.ini`,
  `Dockerfile.backend → backend/Dockerfile`,
  `package.json → frontend/package.json`,
  `package-lock.json → frontend/package-lock.json`,
  `tsconfig.json → frontend/tsconfig.json`,
  `tsconfig.node.json → frontend/tsconfig.node.json`,
  `vite.config.ts → frontend/vite.config.ts`,
  `eslint.config.js → frontend/eslint.config.js`,
  `Dockerfile.frontend → frontend/Dockerfile`; verificar con
  `git status --porcelain` que son renames (`R`) sin contenido modificado y
  que en raíz ya NO existen esos archivos (`ls pyproject.toml alembic.ini
  package.json vite.config.ts Dockerfile.backend Dockerfile.frontend` falla).
- [x] 1.2 Higiene disco: borrar `node_modules/` raíz y `__pycache__/`/`*.pyc`
  huérfanos; verificar `git ls-files | grep -E '__pycache__|\.pyc|node_modules'`
  vacío (nada de eso estuvo trackeado) y `git check-ignore node_modules
  backend/src/app/__pycache__` sigue ignorando.

## 2. Backend: re-apuntes con cwd `backend/`

- [x] 2.1 `backend/pyproject.toml`: `testpaths = ["test"]`,
  `pythonpath = ["src"]`; install pasa a `pip install -e backend/[dev]`
  desde raíz (o `pip install -e .[dev]` con cwd `backend/`); verificar
  import root intacta con `cd backend && python -c "import app.main"` y
  `ruff check src test` en verde con cwd `backend/`.
- [x] 2.2 `backend/alembic.ini`: `script_location = src/app/db/migrations`
  (relativo a `backend/`); documentar cwd canónico `backend/` (prohibido
  `alembic -c backend/alembic.ini` desde raíz); verificar `env.py` resuelve
  a `backend/src` y correr con cwd `backend/` `alembic history` +
  `alembic upgrade head` (baseline `btree_gist`, sin tablas de dominio).
- [x] 2.3 `backend/Dockerfile` (contexto `backend/`): `COPY pyproject.toml
  ./`, `COPY src ./src`, `ENV PYTHONPATH=/srv/src`,
  `CMD ["uvicorn", "app.main:app", …]` intacto; verificar que no nombra
  `backend/src` con prefijo (el contexto ya ES `backend/`).

## 3. Frontend: re-apuntes con cwd `frontend/`

- [x] 3.1 `frontend/package.json` (`lint → eslint src --max-warnings 0`),
  `frontend/tsconfig.json` (`include: ["src", "test"]`),
  `frontend/tsconfig.node.json` (`include: ["vite.config.ts"]`),
  `frontend/eslint.config.js`
  (`files: ["src/**/*.{ts,tsx}", "test/**/*.ts"]`),
  `frontend/vite.config.ts` (`root: "src"`); verificar con cwd `frontend/`
  `npx tsc --noEmit` y `npx eslint src --max-warnings 0` en verde (R7:
  strict, sin `any`).
- [x] 3.2 `frontend/Dockerfile` (contexto `frontend/`): `COPY package.json
  package-lock.json ./`, `COPY vite.config.ts tsconfig.json
  tsconfig.node.json eslint.config.js ./`, `COPY src ./src`, nginx
  `COPY --from=build /srv/src/dist`; reinstalar `node_modules/` en
  `frontend/` (`npm ci` con cwd `frontend/`); verificar `npm run build`
  genera `frontend/src/dist` (coincide con el `COPY` de nginx).
- [x] 3.3 `index.html` ya en `frontend/src/index.html`: sin move; verificar
  que no existe `index.html` en raíz y que el `<script src="/main.tsx">`
  resuelve con `root: "src"`.

## 4. Compose + CI + README (orquestación y docs)

- [x] 4.1 `docker-compose.yml` (queda en raíz): `api`/`worker` con
  `context: backend` + `dockerfile: Dockerfile`, `web` con
  `context: frontend` + `dockerfile: Dockerfile`; healthchecks y
  `depends_on` intactos; verificar `docker compose config` parsea (si no hay
  Docker en la máquina: skip honesto documentado + re-verificación en CI,
  como `restructure-por-lado` task 2.5).
- [x] 4.2 `.github/workflows/ci.yml` (queda en raíz): job backend con
  `working-directory: backend` (`pip install -e .[dev]`,
  `ruff check src test`, `pytest test -q`); job frontend con
  `working-directory: frontend` (`npm ci`, `npx tsc --noEmit`,
  `npx eslint src --max-warnings 0`); verificar YAML parsea y comandos sin
  prefijos cruzados.
- [x] 4.3 `README.md`: actualizar TODOS los comandos dev/test (quickstart,
  desarrollo local, migraciones con cwd `backend/`, tabla de calidad);
  reescribir §Estructura al árbol KB 08 literal (configs dentro de cada
  lado, compose + `.env.example` en raíz); verificar cada bloque `bash`
  ejecutable tal cual está escrito.

## 5. Blindaje con tests de estructura + cierre

- [x] 5.1 Reescribir `backend/test/test_structure.py`: asertar configs en
  cada lado (`backend/pyproject.toml` con `testpaths ["test"]` /
  `pythonpath ["src"]`, `backend/alembic.ini` con
  `src/app/db/migrations`, `backend/Dockerfile`,
  `frontend/package.json`, `frontend/tsconfig*.json`,
  `frontend/vite.config.ts` con `root "src"`, `frontend/eslint.config.js`,
  `frontend/Dockerfile`); prohibir esos archivos en raíz y los nombres
  viejos (`Dockerfile.backend`, `Dockerfile.frontend`); exigir árbol
  `backend/src/app/**`, `frontend/src/**` y cero `.py` productivos fuera de
  `backend/src/`; confirmar `parents[2]` sigue resolviendo a raíz.
- [x] 5.2 Puerta backend (cwd `backend/`): `pytest test -q` y
  `ruff check src test` en verde; stubs siguen importables y `schemas.py`
  recuerdan `extra="forbid"` (R1).
- [x] 5.3 Puerta frontend (cwd `frontend/`): `npx tsc --noEmit`,
  `npx eslint src --max-warnings 0` y `npm run build` en verde (R7).
- [x] 5.4 Barrido final de paths viejos: `grep -rn` de
  `Dockerfile.backend`, `Dockerfile.frontend`, `src/backend`,
  `src/frontend`, `test/backend`, `test/frontend` (y `backend/test` /
  `backend/src` / `frontend/src` con prefijo en configs ya mudadas) vacío
  salvo este change y archivos históricos; `alembic upgrade head` (cwd
  `backend/`) + `docker compose up --build` + `GET /api/health → 200`
  (o sustituto honesto sin Docker + re-verificación en CI).
- [x] 5.5 Checkpoint final LOW: árbol == tabla old→new de `design.md`,
  suite + linters + build + `alembic` + compose verdes, cero lógica de
  negocio agregada, README consistente → change listo para `/opsx:apply`
  (que ejecuta la mudanza) y posterior `/opsx:archive`. Este change salda el
  follow-up opción 2 de `restructure-por-lado`: sin nuevos follow-ups.
