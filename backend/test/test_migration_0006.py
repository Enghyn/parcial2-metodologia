"""Estructura de la migración 0006 (C-10). Sin PostgreSQL: checks estáticos."""
from __future__ import annotations

import re
from pathlib import Path

MIG = Path("src/app/db/migrations/versions/0006_pre_reserva_origen.py")


def test_archivo_existe():
    assert MIG.exists()


def test_revision_y_down_revision():
    src = MIG.read_text(encoding="utf-8")
    assert 'revision: str = "0006_pre_reserva_origen"' in src
    assert 'down_revision' in src
    assert "0005_agenda_indice_inicio" in src


def test_crea_tabla_pre_reservas():
    src = MIG.read_text(encoding="utf-8")
    assert 'create_table(\n        "pre_reservas"' in src or 'create_table("pre_reservas"' in src or '"pre_reservas"' in src
    assert "token" in src
    assert "turnos" in src


def test_agrega_columna_origen_a_turnos():
    src = MIG.read_text(encoding="utf-8")
    assert "origen" in src
    assert "interno" in src


def test_downgrade_reversible():
    src = MIG.read_text(encoding="utf-8")
    assert "def downgrade" in src
    assert "drop_table" in src or "drop_column" in src


def test_tiene_indices():
    src = MIG.read_text(encoding="utf-8")
    assert "create_index" in src or "Index" in src
