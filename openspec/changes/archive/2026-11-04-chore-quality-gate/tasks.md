# Tasks — chore-quality-gate

> **Sin cambio de comportamiento.** El gate debe quedar limpio y la suite debe degradar con skip, no con cuelgue.

## 1. Línea base

- [x] 1.1 Registrar `python -m ruff check src test --statistics` y `python -m pytest -q` con y sin PostgreSQL.
- [x] 1.2 Confirmar que el único bloqueo de colección es `IDS = _seed_ids()` en `test_agenda_router.py:93`.

## 2. Ruff

- [x] 2.1 Correr `python -m ruff check --fix src test` y revisar el diff.
- [x] 2.2 Corregir a mano los 3 `DTZ001` (naive intencional con `# noqa`, o datetime con `UTC`/`tzinfo`).
- [x] 2.3 Verificar `python -m ruff check src test` en cero.

## 3. Suite hermética

- [x] 3.1 Agregar `markers = ["integration: ..."]` en `backend/pyproject.toml`.
- [x] 3.2 Agregar a `backend/test/conftest.py` la fixture `db_disponible` con `connect_timeout=2` y verificación de seed.
- [x] 3.3 Agregar `pytestmark` de integration + `usefixtures("db_disponible")` a `test_agenda_router`, `test_agenda_service`, `test_public_router` y `test_public_service`.
- [x] 3.4 Reemplazar `IDS = _seed_ids()` por un fixture `autouse` de módulo en `test_agenda_router.py`; verificar que la colección no abre conexiones.
- [x] 3.5 Verificar `python -m pytest -m "not integration" -q` **sin** base: debe terminar rápido con skips, no con `OperationalError`.
- [x] 3.6 Verificar `python -m pytest -q` **con** PostgreSQL: toda la suite en verde.

## 4. Documentación

- [x] 4.1 Actualizar `AGENTS.md`/`CLAUDE.md` con los comandos unitarios vs integración y el modo de falla esperado.
- [x] 4.2 Actualizar `README.md` con la misma distinción.
- [x] 4.3 Verificar que `openspec validate "chore-quality-gate" --strict` pasa con `skip_specs: true`.

## Workflow follow-up

- Revisión humana del design antes de aplicar.
- Aplicar y actualizar checkboxes.
- Archivar con `openspec archive "chore-quality-gate" -y`.
