# Design — mudanza-completa-configs

## Context

Ver `proposal.md` (orden + fidelidad KB 08 + costo de fricción diaria).
Estado: `backend/{src,test}` + `frontend/{src,test}` aplicados en working
tree (`restructure-por-lado` complete en `openspec list`);
`refactor-arquitectura-08` aplicado, NO archivado, no se toca.
`frontend/src/index.html` verificado en su lugar (entry ya resuelto desde
el lado). Restricciones vinculantes: R1, R5, R7, R9, R10, R11 (sin commits,
solo working tree), R12, R13. Governance LOW: movimiento mecánico + path
fixes + docs; si tests/CI en verde, autonomía total. Skills aplicables:
`fastapi-templates` (entry `app/main.py`, import root `app.*` — intactos,
solo cambia la raíz física de los manifiestos), `api-and-interface-design`
(contrato intacto, sin cambios), `postgresql-table-design` (baseline
`btree_gist` intacta), `async-python-patterns` (sin cambios de runtime),
Tailwind v4 CSS-first + `vercel-react-best-practices` (sin barrels nuevos).

## Goals / Non-Goals

**Goals:**

- Árbol KB 08 literal: cada lado contiene su código, sus tests y sus
  manifiestos; todas las herramientas (`pytest`, `ruff`, `tsc`, `eslint`,
  `alembic`, Docker, CI) en verde desde su cwd canónico.
- Cero regresión: suite backend, `ruff`, `tsc`, `eslint`, `vite build`,
  `alembic upgrade head`, `docker compose config` y `GET /api/health` en
  compose idénticos.

**Non-Goals:**

- Modelos, migraciones de dominio, JWT/RBAC, adapters, workers,
  superficies: todo eso es C-02+. Ningún stub gana lógica.
- Cambiar contratos, variables de entorno, dependencias o versiones.
- Crear `.env` real ni tocar secretos.

## Decisions

- **Tabla old → new (vinculante, opción 2):**

  | Antes (raíz) | Después | Notas |
  |---|---|---|
  | `pyproject.toml` | `backend/pyproject.toml` | `testpaths = ["test"]`, `pythonpath = ["src"]` (relativos a `backend/`); install `pip install -e backend/[dev]` desde raíz o `pip install -e .[dev]` con cwd `backend/` |
  | `alembic.ini` | `backend/alembic.ini` | `script_location = src/app/db/migrations` (relativo a `backend/`); cwd canónico `backend/` (ver decisión alembic) |
  | `Dockerfile.backend` | `backend/Dockerfile` | Renombre canónico KB 08; contexto `backend/`: `COPY pyproject.toml ./`, `COPY src ./src`, `ENV PYTHONPATH=/srv/src`, `CMD uvicorn app.main:app` intacto |
  | `package.json` + `package-lock.json` | `frontend/package.json` + `frontend/package-lock.json` | `lint → eslint src --max-warnings 0`; `npm` con cwd `frontend/` (`npm --prefix frontend …` solo como fallback) |
  | `tsconfig.json` | `frontend/tsconfig.json` | `include: ["src", "test"]` (R7 strict intacto) |
  | `tsconfig.node.json` | `frontend/tsconfig.node.json` | `include: ["vite.config.ts"]` (contenido intacto, resuelve junto a la config) |
  | `vite.config.ts` | `frontend/vite.config.ts` | `root: "src"` (la config ya vive en `frontend/`) |
  | `eslint.config.js` | `frontend/eslint.config.js` | `files: ["src/**/*.{ts,tsx}", "test/**/*.ts"]` sin prefijos (R7: `no-explicit-any` intacto) |
  | `Dockerfile.frontend` | `frontend/Dockerfile` | Renombre canónico; contexto `frontend/`: `COPY package.json package-lock.json ./`, `COPY vite.config.ts tsconfig.json tsconfig.node.json eslint.config.js ./`, `COPY src ./src`, nginx `COPY --from=build /srv/src/dist` |
  | `docker-compose.yml`, `.env.example`, `.github/workflows/` | **QUEDAN en raíz** | Ver justificación por archivo abajo |
  | `README.md`, `CHANGES.md`, `AGENTS.md`/`CLAUDE.md`, `skills-lock.json`, `.gitignore`, `openspec/`, `.atl/`, `docs/`, `knowledge-base/` | **QUEDAN en raíz** | Documentación y tooling a nivel repo, no de lado |

- **Decisión UNA — contextos compose: por lado, no raíz.** `api`/`worker`:
  `context: backend`, `dockerfile: Dockerfile`; `web`: `context: frontend`,
  `dockerfile: Dockerfile`. Alternativa (contexto raíz `.` + `dockerfile:
  backend/Dockerfile`) descartada: obligaría a `COPY backend/src …` con
  prefijos eternos y contradice el espíritu "cada lado autocontenido" de la
  opción 2. Topología intacta: healthchecks y `depends_on` no se tocan.
- **Decisión UNA — cwd backend: `backend/`.** `pytest` y `ruff` descubren
  `backend/pyproject.toml` corriendo con cwd `backend/`
  (`pytest test -q`, `ruff check src test`); desde raíz solo con flags
  explícitos (`pytest -c backend/pyproject.toml`,
  `pip install -e backend/[dev]`). CI backend usa
  `working-directory: backend` y comandos sin prefijos.
- **Decisión UNA — cwd alembic: `backend/` siempre.** Con
  `script_location = src/app/db/migrations` (relativo), `alembic` DEBE
  correrse con cwd `backend/`; `alembic -c backend/alembic.ini` desde raíz
  queda PROHIBIDO (resolvería `root/src/…` inexistente). `env.py`: el
  `sys.path.insert` con 4× `dirname` desde
  `…/app/db/migrations/env.py` resuelve a `backend/src` automáticamente
  (misma profundidad relativa que antes) — verificar por ejecución, no
  asumir.
- **Decisión UNA — cwd frontend: `frontend/`.** `npm ci`, `npx tsc
  --noEmit`, `npx eslint src --max-warnings 0`, `npm run build` con cwd
  `frontend/`; CI frontend usa `working-directory: frontend`.
  `node_modules/` se reinstala en `frontend/`; el de raíz (ignorado, no
  trackeado) se elimina del disco.
- **Decisión UNA — `index.html`: no se mueve.** Ya vive en
  `frontend/src/index.html` con `<script src="/main.tsx">`; con
  `root: "src"` el entry resuelve a `frontend/src/index.html` + `/main.tsx`
  sin cambios. No existe `index.html` en raíz: nada que verificar.
- **Decisión UNA — `.env.example`: único, en raíz.** Es la plantilla
  visible al entrar (`cp .env.example .env`) y la que consume
  `docker-compose.yml`; ya contiene vars de ambos lados (incl.
  `VITE_API_URL` del frontend). Fraccionarlo en dos archivos escondería la
  mitad de la configuración y rompería el quickstart. Sin secretos: solo
  placeholders (R9 intacto).
- **Justificación por archivo que queda en raíz:** `docker-compose.yml` —
  KB 08 §Estructura lo dibuja en raíz orquestando los cinco servicios;
  `​.env.example` — decisión anterior; `.github/workflows/` — GitHub Actions
  solo descubre workflows bajo `.github/workflows/` en raíz;
  `README.md`/`CHANGES.md`/`AGENTS.md`/`CLAUDE.md` — documentación a nivel
  repo; `skills-lock.json`/`.gitignore` — tooling a nivel repo;
  `openspec/`/`.atl/`/`docs/`/`knowledge-base/` — fuentes de verdad y
  estado del proyecto, no artefactos de build de ningún lado.
- **Import root `app.*` intacta + `PYTHONPATH`:** dev local
  `PYTHONPATH=backend/src` (documentado en README); Docker
  `ENV PYTHONPATH=/srv/src` (contexto `backend/`, `COPY src ./src`).
  `CMD ["uvicorn", "app.main:app", …]` no se toca.
- **`test/backend/test_structure.py` reescrito (misma ruta):** `ROOT =
  Path(__file__).resolve().parents[2]` sigue resolviendo a raíz
  (`backend/test/X.py` → `[0]=test`, `[1]=backend`, `[2]=raíz`). Nuevas
  aserciones: `backend/pyproject.toml` (`testpaths == ["test"]`,
  `pythonpath == ["src"]`), `backend/alembic.ini`
  (`src/app/db/migrations`), `backend/Dockerfile`, `frontend/package.json`,
  `frontend/{tsconfig.json,tsconfig.node.json,vite.config.ts,eslint.config.js,Dockerfile}`,
  `vite root == "src"`; prohibiciones: esos mismos archivos en raíz,
  `Dockerfile.backend`/`Dockerfile.frontend` viejos, `pyproject`/`package`
  en raíz.

## Risks / Trade-offs

- [Riesgo] Referencia de path olvidada (CI, Dockerfile, `env.py`,
  `tsconfig.node.json`, README) → Mitigación: barrido
  `grep -rn "Dockerfile.backend\|Dockerfile.frontend\|src/backend\|src/frontend\|test/backend\|test/frontend\|backend/test\|backend/src\|frontend/src"`
  acotado a configs debe salir vacío de paths viejos (salvo este change e
  histórico), y cada puerta de tasks corre la herramienta real desde su cwd.
- [Riesgo] `alembic` corrido desde raíz con `-c` (script_location relativo
  roto) → Mitigación: decisión UNA documentada + `test_structure.py` exige
  `src/app/db/migrations` en `backend/alembic.ini` + task corre
  `alembic upgrade head` con cwd `backend/`.
- [Riesgo] `node_modules/` raíz fantasma usado por error tras el move →
  Mitigación: eliminarlo del disco, reinstalar en `frontend/`, verificar
  `npm run build` genera `frontend/src/dist` (coincide con nginx `COPY`).
- [Riesgo] Contextos por lado rompen `.dockerignore`/COPY →
  Mitigación: `docker compose config` + build de ambas imágenes en la task
  de compose (o skip honesto sin Docker + re-verificación en CI, como hizo
  `restructure-por-lado` task 2.5).
- [Trade-off] Fricción diaria con prefijos/cwd (costo declarado en
  proposal) → aceptado: es el precio de la fidelidad KB 08; el README deja
  todos los comandos nuevos por escrito.

## Migration Plan

Sin despliegue ni datos: `git mv` a cada lado en working tree (R11: sin
commit). Orden apply: 1) `git mv` de manifiestos/configs + renombres
`Dockerfile.backend→backend/Dockerfile`,
`Dockerfile.frontend→frontend/Dockerfile`; 2) editar contenidos
(`pyproject`, `alembic.ini`, `vite`, `tsconfig*`, `eslint`, `package.json`,
Dockerfiles, compose, CI, README); 3) reinstalar `node_modules` en
`frontend/`, borrar `node_modules/` y `__pycache__` raíz del disco;
4) reescribir `test_structure.py`; 5) correr puertas (tasks). Rollback =
`git checkout` + `git clean -fd` del working tree (nada commiteado, nada
migrado). Checkpoint LOW: suite + linters + build + `alembic` + compose
verdes → listo para `/opsx:apply` y posterior `/opsx:archive`.

## Open Questions

Ninguna que cambie specs, enfoque o tasks. `.env.example` único en raíz vs
fraccionado queda decidido (único en raíz); si un change futuro necesita
vars solo-frontend sensibles, lo revisita ese change, no este.
