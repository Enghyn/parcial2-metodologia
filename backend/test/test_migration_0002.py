"""Migración 0002: encadenada al baseline, nueve tablas e índices de agenda."""
import re
from pathlib import Path

from sqlalchemy import CheckConstraint, Column, Integer, MetaData, Table

from app.db.base import NAMING_CONVENTION
from app.db.registry import Base

ROOT = Path(__file__).resolve().parents[2]
VERSIONES = ROOT / "backend" / "src" / "app" / "db" / "migrations" / "versions"
ARCHIVO = VERSIONES / "0002_core_models.py"

# Alembic expande los nombres cortos con la convención de `Base.metadata`.
CHECKS = {
    "ck_usuarios_rol": "rol",
    "ck_profesionales_duracion": "duracion",
    "ck_turnos_rango": "rango",
    "ck_turnos_duracion": "duracion",
    "ck_turnos_estado": "estado",
    "ck_turnos_sena": "sena",
    "ck_bloqueos_recurso": "recurso",
    "ck_bloqueos_rango": "rango",
    "ck_hallazgos_pieza_pieza_fdi": "pieza_fdi",
    "ck_hallazgos_pieza_estado": "estado",
    "ck_movimientos_caja_monto": "monto",
    "ck_movimientos_caja_tipo": "tipo",
    "ck_movimientos_caja_medio_pago": "medio_pago",
}


def _texto() -> str:
    return ARCHIVO.read_text(encoding="utf-8")


def test_la_migracion_existe() -> None:
    assert ARCHIVO.is_file(), "falta la migración 0002_core_models.py"


def test_revision_encadenada_al_baseline() -> None:
    texto = _texto()
    assert 'revision: str = "0002_core_models"' in texto
    assert 'down_revision: str | None = "0001_baseline"' in texto


def test_crea_las_mismas_tablas_que_la_metadata() -> None:
    creadas = set(re.findall(r'op\.create_table\(\s*"([a-z_]+)"', _texto()))
    tablas_0002 = set(Base.metadata.tables) - {"pre_reservas"}
    assert creadas == tablas_0002


def test_declara_constraints_e_indices_de_agenda() -> None:
    texto = _texto()
    faltantes = [final for final, corto in CHECKS.items() if f'name="{corto}"' not in texto]
    assert faltantes == [], f"CHECK ausentes en la migración: {faltantes}"
    for nombre in (
        "pk_usuarios",
        "uq_usuarios_email",
        "uq_profesionales_matricula",
        "ix_turnos_sillon_inicio_fin",
        "ix_turnos_profesional_inicio_fin",
        "uq_hallazgos_pieza_odontograma_pieza",
    ):
        assert nombre in texto, f"falta {nombre} en la migración"


def test_los_nombres_cortos_expanden_a_los_nombres_finales() -> None:
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    tabla = Table(
        "turnos",
        metadata,
        Column("id", Integer, primary_key=True),
        CheckConstraint("fin > inicio", name="rango"),
    )
    nombres = {c.name for c in tabla.constraints if isinstance(c, CheckConstraint)}
    assert nombres == {"ck_turnos_rango"}


def test_downgrade_revierte_solo_las_tablas_de_dominio() -> None:
    texto = _texto()
    assert texto.count("op.drop_table(") == 9
    assert "DROP EXTENSION" not in texto, "el downgrade no debe tocar btree_gist (baseline)"
