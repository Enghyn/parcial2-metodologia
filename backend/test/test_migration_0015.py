"""Migración 0015: `cierres_caja.estado` de ENUM nativo a varchar(20) + CHECK (C-12b).

Sin PostgreSQL: checks estáticos sobre el texto de la migración, en el estilo de
`test_migration_0004.py` … `test_migration_0006.py`.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSIONES = ROOT / "backend" / "src" / "app" / "db" / "migrations" / "versions"
ARCHIVO = VERSIONES / "0015_cierres_estado_varchar.py"

REVISION = "0015_cierres_estado_varchar"
DOWN_REVISION = "0014_pagos_simulados"
MAX_REVISION_LEN = 32
CATALOGO = "'pendiente', 'cerrado', 'reabierto'"


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
    assert len(REVISION) <= MAX_REVISION_LEN, (
        f"{REVISION} supera los {MAX_REVISION_LEN} caracteres de alembic_version.version_num"
    )


def test_upgrade_convierte_la_columna_a_varchar_20() -> None:
    upgrade = _upgrade()
    assert "op.alter_column(" in upgrade
    assert '"cierres_caja"' in upgrade and '"estado"' in upgrade
    assert "type_=sa.String(20)" in upgrade, "el tipo destino debe ser varchar(20)"
    assert 'postgresql_using="estado::text"' in upgrade, (
        "hace falta el USING explícito para castear el ENUM a texto"
    )


def test_upgrade_quita_y_restablece_el_default() -> None:
    upgrade = _upgrade()
    assert "server_default=None" in upgrade, (
        "debe hacer DROP DEFAULT antes del ALTER TYPE para no arrastrar el default del ENUM"
    )
    assert 'server_default="pendiente"' in upgrade, (
        "el default debe quedar restablecido como texto 'pendiente'"
    )


def test_upgrade_elimina_el_tipo_estado_cierre() -> None:
    upgrade = _upgrade()
    assert 'op.execute("DROP TYPE IF EXISTS estado_cierre")' in upgrade
    assert 'CREATE TYPE estado_cierre' not in upgrade, (
        "el upgrade no debe recrear el ENUM"
    )


def test_upgrade_agrega_el_check_del_catalogo() -> None:
    upgrade = _upgrade()
    assert "op.create_check_constraint(" in upgrade
    assert '"estado"' in upgrade and '"cierres_caja"' in upgrade
    assert f"estado IN ({CATALOGO})" in upgrade


def test_downgrade_elimina_el_check_y_quita_el_default() -> None:
    downgrade = _downgrade()
    assert 'op.drop_constraint("estado", "cierres_caja"' in downgrade
    assert "server_default=None" in downgrade, (
        "el downgrade debe quitar el default de texto antes de volver al ENUM"
    )


def test_downgrade_recrea_el_tipo_y_vuelve_el_enum() -> None:
    downgrade = _downgrade()
    assert f"CREATE TYPE estado_cierre AS ENUM ({CATALOGO})" in downgrade, (
        "el downgrade debe recrear el tipo estado_cierre con el catálogo original"
    )
    assert 'name="estado_cierre"' in downgrade
    assert 'postgresql_using="estado::estado_cierre"' in downgrade, (
        "el cast de vuelta al ENUM debe ser explícito"
    )
    assert 'server_default="pendiente"' in downgrade, (
        "el downgrade debe restaurar el default 'pendiente'"
    )


def test_sin_tenant_id() -> None:
    assert "tenant_id" not in _texto(), "R2: el sistema es mono-consultorio, sin tenant_id"
