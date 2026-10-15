# Proposal — mudanza-completa-configs

## Why

Orden explícita del usuario: ejecutar la **opción 2 ("mudanza completa")**
declarada como follow-up fuera de scope en
`openspec/changes/restructure-por-lado/proposal.md` (Impact: *"mover
manifiestos y configs a `backend/`/`frontend/` … se propone como change
posterior independiente"*). Este change **salda ese follow-up**: mueve
manifiestos, configs y Dockerfiles DENTRO de `backend/` y `frontend/`,
revierte la desviación documentada de `restructure-por-lado/design.md`
("Configs en raíz", tabla old→new: *"SE QUEDAN en raíz … opción 2 futura"*)
y deja `knowledge-base/08_arquitectura_propuesta.md` §Estructura cumplido
**al pie de la letra** (`backend/Dockerfile`, `backend/pyproject.toml`,
`frontend/Dockerfile`, `frontend/vite.config.ts`).

Porqué ahora: `restructure-por-lado` está aplicado en working tree
(`backend/{src,test}` + `frontend/{src,test}` existen, `src/` y `test/` raíz
eliminadas) y sus puertas pasaron; el árbol por lado ya es el contenedor
canónico, así que cada lado puede recibir sus propios manifiestos sin
re-mapear código. `refactor-arquitectura-08` (aplicado, NO archivado) no se
toca: este es un change SEPARADO que solo re-mapea los paths que ese change
y `restructure-por-lado` asumieron en raíz.

Costo honesto: cada lado pasa a tener su propio cwd (`backend/`,
`frontend/`). El trabajo diario gana fricción explícita — `pip install -e
backend/[dev]` o `cd backend`, `npm --prefix frontend …` o
`working-directory: frontend` en CI, `alembic -c backend/alembic.ini` solo
con cwd `backend/` — a cambio de fidelidad total al KB 08 y lados
autocontenidos (cada `Dockerfile` buildea con el contexto de su lado). Nada
de esto cambia comportamiento: import root `app.*`, `uvicorn app.main:app`,
`GET /api/health`, healthchecks y `depends_on` quedan intactos.

## What Changes

- **Mover ADENTRO con `git mv` (mecánico, cero lógica):**
  `pyproject.toml`, `alembic.ini`, `Dockerfile.backend→Dockerfile` a
  `backend/`; `package.json`, `package-lock.json`, `tsconfig.json`,
  `tsconfig.node.json`, `vite.config.ts`, `eslint.config.js`,
  `Dockerfile.frontend→Dockerfile` a `frontend/`. `index.html` ya vive en
  `frontend/src/index.html` (verificado) — no se mueve, el entry se resuelve
  desde `frontend/` con `vite root: "src"`.
- **Re-apuntar herramientas (solo paths, cero negocio):** `pyproject`
  (`testpaths=["test"]`, `pythonpath=["src"]`, relativos a `backend/`);
  `alembic.ini` (`script_location = src/app/db/migrations`, cwd canónico
  `backend/`); `vite root: "src"`; `tsconfig include: ["src","test"]`;
  `eslint files` sin prefijos; `package.json lint → eslint src`;
  Dockerfiles con `COPY` sobre su propio contexto + `PYTHONPATH=/srv/src`;
  compose con **contextos por lado** (`context: backend` /
  `context: frontend`, `dockerfile: Dockerfile`); CI con
  `working-directory` por lado; `README.md` con TODOS los comandos
  actualizados (docs, parte del change).
- **QUEDAN en raíz** (justificados en `design.md`): `docker-compose.yml`
  (KB 08 lo pone en raíz), `.env.example` (plantilla visible al entrar, ya
  contiene vars de ambos lados incl. `VITE_API_URL`), `.github/workflows/`
  (GitHub lo exige en raíz), más `README.md`, `CHANGES.md`, `AGENTS.md` /
  `CLAUDE.md`, `skills-lock.json`, `.gitignore`, `openspec/`, `.atl/`,
  `docs/`, `knowledge-base/`.
- **Reescribir `backend/test/test_structure.py`** para asertar el layout
  nuevo (configs en cada lado, ausencia en raíz) y prohibir el viejo.
- **Limpieza documentada:** `node_modules/` raíz (ignorado, no trackeado)
  se elimina del disco y se reinstala en `frontend/`; `__pycache__` raíz
  igual si existe.
- **No toca:** ningún modelo, migración de dominio, endpoint, JWT/RBAC,
  adapters, workers, forma de error, settings, superficie pública, variables
  de entorno ni comportamiento en runtime. C-02 (`core-models-tenancy`,
  `CHANGES.md`: modelos `Tenant/Usuario/Profesional/Sillon/Paciente` +
  migración 001) no se invade: cero modelos/negocio.

## Relación con KB 08 §Estructura

Se adopta **literal**: `backend/` contiene `Dockerfile` + `pyproject.toml`
(+ `alembic.ini`); `frontend/` contiene `Dockerfile` + `vite.config.ts`
(+ `package.json`, `tsconfig`, `eslint`); `docker-compose.yml` queda en
raíz — exactamente como el árbol del KB 08. La desviación "configs en raíz"
de `restructure-por-lado` queda **revertida y cerrada**, no como deuda
silenciosa sino como este change aplicado.

## Capabilities

### New Capabilities

Ninguna — re-layout puro de configs sin cambio de comportamiento observable.

### Modified Capabilities

Los tres requirements de layout/tooling versionados cambian de paths (sin
cambiar comportamiento): `backend-foundation` (código + configs backend en
`backend/`), `frontend-foundation` (código + configs frontend en
`frontend/`) y `local-platform` (tooling alineado: contextos por lado, CI
con `working-directory`, `.env.example` único en raíz). Deltas en `specs/`
— este change NO declara `skip_specs`.

## Impact

- **Código afectado:** solo ubicación de manifiestos/configs + referencias
  de paths en Dockerfiles, CI, `test_structure.py`, `env.py` (si aplica) y
  `README.md`. `GET /api/health`, settings, forma de error, baseline
  Alembic y topología compose (healthchecks, `depends_on`) intactos.
- **Convivencia con el roadmap:** previo a C-02, higiene transversal igual
  que `refactor-arquitectura-08` y `restructure-por-lado`. No figura en
  `CHANGES.md`; no duplica C-02 (corte: si un archivo necesitaría un import
  de negocio, un modelo o una firma real → no pertenece a este change).
- **Follow-up que se salda:** la opción 2 de `restructure-por-lado` deja de
  estar pendiente cuando este change se aplica. Sin nuevos follow-ups
  declarados.
