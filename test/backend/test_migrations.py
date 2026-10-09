"""Task 1.3 — Alembic inicializado con baseline que habilita btree_gist (layout §5).

Canónico §5: alembic.ini en raíz con script_location = src/backend/app/db/migrations.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_alembic_ini_y_env_existen() -> None:
    assert (ROOT / "alembic.ini").is_file()
    assert (ROOT / "src" / "backend" / "app" / "db" / "migrations" / "env.py").is_file()


def test_baseline_habilita_btree_gist() -> None:
    versions = ROOT / "src" / "backend" / "app" / "db" / "migrations" / "versions"
    assert versions.is_dir()
    candidates = list(versions.glob("*.py"))
    assert candidates != [], "sin migraciones"
    contenido = "\n".join(p.read_text(encoding="utf-8") for p in candidates)
    assert "btree_gist" in contenido
    assert "CREATE EXTENSION" in contenido
