# Proposal — chore-quality-gate

## Why

El repositorio no pasa su propio gate de calidad: `ruff check src test` reporta **77 errores** (56 `UP017`, 10 imports sin usar, 4 imports desordenados, 3 `DTZ001`, etc.) y `pytest` **sin PostgreSQL** no arranca: la colección se cuelga entre 2 y 4 minutos y termina en `OperationalError`. Eso impide que un compañero nuevo corra la suite sin levantar una base.

## What Changes

- `ruff --fix` sobre `src` y `test`, más los 3 `DTZ001` manuales (naive intencional con `# noqa` o datetime aware).
- Marcar los tests que requieren PostgreSQL como `integration` y saltearlos rápido si no hay base o seed (fixture con `connect_timeout` corto).
- Mover `IDS = _seed_ids()` de `test_agenda_router.py` a un fixture de módulo, para que la colección no abra conexiones.
- Configurar el marker `integration` en `backend/pyproject.toml`.
- Documentar en `AGENTS.md`/`README.md` cómo correr solo unitarios (`pytest -m "not integration"`) y la suite completa con base.

## Capabilities

### New Capabilities

- Ninguna.

### Modified Capabilities

- Ninguna: es tooling y tests, sin cambio de comportamiento observable. El change usa `skip_specs: true`.

## Impact

- **Tests**: `backend/test/*` (markers, fixture, limpieza de imports).
- **Tooling**: `backend/pyproject.toml` (markers), `ruff` y documentación.
- **Sin cambios de API, modelos, migraciones ni frontend.**
- **Fuera de alcance**: agregar CI con PostgreSQL (`.github/` está ignorado) y tests de frontend.
