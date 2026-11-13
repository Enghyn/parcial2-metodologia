"""Migración 0016: tabla `auditorias` (C-20)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSIONES = ROOT / "backend" / "src" / "app" / "db" / "migrations" / "versions"
ARCHIVO = VERSIONES / "0016_auditoria.py"

REVISION = "0016_auditoria"
DOWN_REVISION = "0015_cierres_estado_varchar"
MAX_REVISION_LEN = 32


def _texto() -> str:
    return ARCHIVO.read_text(encoding="utf-8")


def _upgrade() -> str:
    return _texto().split("def upgrade() -> None:", maxsplit=1)[-1].split(
        "def downgrade() -> None:", maxsplit=1
    )[0]


def _downgrade() -> str:
    return _texto().split("def downgrade() -> None:", maxsplit=1)[-1]


def test_la_migracion_existe() -> None:
    assert ARCHIVO.is_file(), f"falta {ARCHIVO.name}"


def test_revision_encadenada_y_dentro_del_limite() -> None:
    texto = _texto()
    assert f'revision: str = "{REVISION}"' in texto
    assert f'down_revision: str | None = "{DOWN_REVISION}"' in texto
    assert len(REVISION) <= MAX_REVISION_LEN


def test_upgrade_crea_tabla_auditorias() -> None:
    upgrade = _upgrade()
    assert "op.create_table(" in upgrade
    assert '"auditorias"' in upgrade


def test_upgrade_define_checks_accion_y_recurso() -> None:
    upgrade = _upgrade()
    assert "accion" in upgrade
    assert "recurso" in upgrade


def test_upgrade_define_indices() -> None:
    upgrade = _upgrade()
    assert "op.create_index(" in upgrade
    assert "fecha" in upgrade
    assert "usuario_id" in upgrade


def test_downgrade_elimina_tabla() -> None:
    downgrade = _downgrade()
    assert 'op.drop_table("auditorias")' in downgrade


def test_sin_tenant_id() -> None:
    assert "tenant_id" not in _texto()
