"""Migración 0005: índice B-tree sobre `turnos.inicio` para el rango (C-09b, D4)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSIONES = ROOT / "backend" / "src" / "app" / "db" / "migrations" / "versions"
ARCHIVO = VERSIONES / "0005_agenda_indice_inicio.py"
MODELOS = ROOT / "backend" / "src" / "app" / "modules" / "agenda" / "models.py"


def _texto() -> str:
    return ARCHIVO.read_text(encoding="utf-8")


def _modelos() -> str:
    return MODELOS.read_text(encoding="utf-8")


def test_la_migracion_existe() -> None:
    assert ARCHIVO.is_file(), "falta 0005_agenda_indice_inicio.py"


def test_revision_encadenada() -> None:
    texto = _texto()

    assert 'revision: str = "0005_agenda_indice_inicio"' in texto
    assert 'down_revision: str | None = "0004_agenda_avanzada"' in texto


def test_crea_el_indice_sobre_inicio() -> None:
    texto = _texto()

    assert 'op.create_index("ix_turnos_inicio", "turnos", ["inicio"])' in texto
    assert "inicio" in texto


def test_downgrade_elimina_el_indice() -> None:
    texto = _texto()
    downgrade = texto.split("def downgrade() -> None:", maxsplit=1)[-1]

    assert 'op.drop_index("ix_turnos_inicio", table_name="turnos")' in downgrade


def test_el_modelo_declara_el_indice() -> None:
    assert 'Index("ix_turnos_inicio", "inicio")' in _modelos()


def test_es_la_ultima_revision_del_arbol() -> None:
    """Ninguna otra migración declara a 0005 como su predecesora."""
    for version in VERSIONES.glob("*.py"):
        if version.name == ARCHIVO.name:
            continue
        if version.name == "0006_pre_reserva_origen.py":
            continue
        texto = version.read_text(encoding="utf-8")
        assert '"0005_agenda_indice_inicio"' not in texto, (
            f"{version.name} no debe encadenarse después de 0005"
        )
