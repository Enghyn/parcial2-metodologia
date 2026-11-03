"""Migración 0003: constraints de hardening y triggers de defensa en base."""
from pathlib import Path

from app.db.registry import Base

ROOT = Path(__file__).resolve().parents[2]
VERSIONES = ROOT / "backend" / "src" / "app" / "db" / "migrations" / "versions"
ARCHIVO = VERSIONES / "0003_core_data_model_hardening.py"

CONSTRAINTS = (
    "ck_usuarios_email_normalizado",
    "ck_bloqueos_motivo_no_vacio",
    "ck_turnos_fin_coherente",
)

FUNCIONES = ("fn_forbid_ledger_mutation", "fn_forbid_physical_delete")

TRIGGERS = (
    "trg_movimientos_caja_inmutable",
    "trg_movimientos_caja_no_truncate",
    "trg_pacientes_no_delete",
    "trg_pacientes_no_truncate",
    "trg_turnos_no_delete",
    "trg_turnos_no_truncate",
    "trg_profesionales_no_delete",
    "trg_profesionales_no_truncate",
    "trg_sillones_no_delete",
    "trg_sillones_no_truncate",
)


def _texto() -> str:
    return ARCHIVO.read_text(encoding="utf-8")


def test_la_migracion_existe() -> None:
    assert ARCHIVO.is_file(), "falta la migración 0003_core_data_model_hardening.py"


def test_revision_encadenada_a_0002() -> None:
    texto = _texto()
    assert 'revision: str = "0003_core_data_model_hardening"' in texto
    assert 'down_revision: str | None = "0002_core_models"' in texto


def test_aplica_los_tres_constraints() -> None:
    texto = _texto()
    faltantes = [c for c in CONSTRAINTS if c not in texto]
    assert faltantes == [], f"constraints ausentes: {faltantes}"


def test_crea_funciones_y_triggers() -> None:
    texto = _texto()
    faltantes = [t for t in TRIGGERS if t not in texto]
    assert faltantes == [], f"triggers ausentes: {faltantes}"
    for funcion in FUNCIONES:
        assert funcion in texto, f"falta la función {funcion}"
    assert texto.count("CREATE TRIGGER") == 10
    assert texto.count("CREATE OR REPLACE FUNCTION") == 2


def test_downgrade_elimina_todo_lo_agregado() -> None:
    texto = _texto()
    assert texto.count("DROP TRIGGER IF EXISTS") == 10
    assert texto.count("DROP FUNCTION IF EXISTS") == 2
    assert texto.count("DROP CONSTRAINT IF EXISTS") == 3
    assert "DROP TABLE" not in texto, "0003 no debe tocar las tablas de C-02"
    assert "btree_gist" not in texto


def test_la_metadata_sigue_siendo_la_fuente_de_las_tablas() -> None:
    creadas = set(__import__("re").findall(r'op\.create_table\(\s*"([a-z_]+)"', _texto()))
    assert creadas == set(), "0003 solo altera; no crea tablas"
    assert set(Base.metadata.tables) >= {"usuarios", "bloqueos", "turnos", "movimientos_caja"}
