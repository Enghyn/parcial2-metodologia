"""Migración 0004: agenda avanzada (sobreturnos y ausente)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSIONES = ROOT / "backend" / "src" / "app" / "db" / "migrations" / "versions"
ARCHIVO = VERSIONES / "0004_agenda_avanzada.py"


def _texto() -> str:
    return ARCHIVO.read_text(encoding="utf-8")


def test_la_migracion_existe() -> None:
    assert ARCHIVO.is_file(), "falta 0004_agenda_avanzada.py"


def test_revision_encadenada() -> None:
    texto = _texto()
    assert 'revision: str = "0004_agenda_avanzada"' in texto
    assert 'down_revision: str | None = "0003_core_data_model_hardening"' in texto


def test_agrega_columnas_y_constraints() -> None:
    texto = _texto()
    for nombre in (
        "es_sobreturno",
        "motivo_sobreturno",
        "autorizado_por",
        "ck_turnos_estado",
        "ck_turnos_sobreturno_motivo",
        "fk_turnos_autorizado_por_usuarios",
    ):
        assert nombre in texto, f"falta {nombre}"


def test_downgrade_revierte_lo_agregado() -> None:
    texto = _texto()
    assert "DROP CONSTRAINT IF EXISTS ck_turnos_sobreturno_motivo" in texto
    assert "DROP CONSTRAINT IF EXISTS fk_turnos_autorizado_por_usuarios" in texto
    assert "WHERE estado = 'ausente'" in texto, "downgrade debe mapear ausente a cancelado"
    for columna in ("autorizado_por", "motivo_sobreturno", "es_sobreturno"):
        assert f"DROP COLUMN IF EXISTS {columna}" in texto
