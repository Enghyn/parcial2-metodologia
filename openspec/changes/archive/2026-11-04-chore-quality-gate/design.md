# Design — chore-quality-gate

## Context

Ver `proposal.md` — Why. La suite tiene 224 tests que pasan con PostgreSQL 17 (224 passed, 7 skipped), pero el gate local no está limpio: `ruff` reporta 77 errores y la colección sin base falla por `IDS = _seed_ids()` en `test_agenda_router.py:93`. Los tests de integración son válidos; el problema es cómo fallan y cómo se ejecutan.

## Goals / Non-Goals

**Goals:**

- `ruff check src test` en cero.
- `pytest -m "not integration"` corre rápido sin PostgreSQL.
- `pytest` completo corre con PostgreSQL y no pierde cobertura.

**Non-Goals:**

- Cambiar comportamiento de producto.
- Agregar CI (`.github/` no se versiona).
- Tests de frontend.

## Decisions

### D1 — Ruff: automático + manual

`ruff check --fix src test` resuelve 74 errores. Los 3 `DTZ001` se revisan a mano:
- el naive intencional de `test_timezone.py` lleva `# noqa: DTZ001` (prueba la normalización);
- los otros dos se corrigen con `UTC` o `tzinfo` explícito.

- **Por qué**: mantener el diff mecánico y revisar solo los casos semánticos.
- **Alternativa descartada**: desactivar reglas en `pyproject.toml` (oculta el problema).

### D2 — Marker `integration` + fixture `db_disponible`

- `pyproject.toml`: `markers = ["integration: requiere PostgreSQL migrado y sembrado"]`.
- `conftest.py`: fixture de sesión `db_disponible` que hace `select 1` con `connect_args={"connect_timeout": 2}` y verifica que haya sillones sembrados; si falla, `pytest.skip`.
- Los módulos `test_agenda_router`, `test_agenda_service`, `test_public_router` y `test_public_service` llevan `pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("db_disponible")]`.
- `test_agenda_router.py` reemplaza `IDS = _seed_ids()` por un fixture `autouse` de módulo que llena `IDS` después de `db_disponible`.

- **Por qué**: la colección no debe tocar la base; el skip debe ser inmediato y explicable.
- **Alternativa descartada**: borrar los tests de integración (perdería RN-AG-01/RBAC contra DB real).

### D3 — Documentación

`AGENTS.md` y `README.md` agregan:
- `python -m pytest -m "not integration" -q` para unitarios sin base;
- `python -m pytest -q` para la suite completa (requiere `alembic upgrade head` + seed);
- el modo de falla esperado: skip, no cuelgue.

### D4 — Sin spec

No cambia comportamiento observable; el change usa `skip_specs: true` en `.openspec.yaml`.

## Risks / Trade-offs

- [Marcar integration puede ocultar fallos si nadie corre la suite completa] → se documenta y se corre en la verificación; el CI futuro deberá levantar Postgres.
- [`--fix` toca muchos archivos] → se revisa el diff y se corre la suite completa después.
- [Fixture con seed] → si la base está vacía, skip con mensaje “ejecutá el seed”; no es un fallo del código.

## Migration Plan

1. `ruff check --fix` + manuales.
2. Fixture/marker + mover `IDS`.
3. Verificar sin DB (rápido, skips) y con DB (224+ passed).
4. Actualizar docs.

## Open Questions

- ¿Se versiona `.github/workflows` en el futuro para correr integración? Fuera de alcance.
