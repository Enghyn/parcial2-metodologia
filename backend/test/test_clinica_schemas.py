"""TDD C-07 — schemas de ficha clínica (R1 extra='forbid')."""
from datetime import date

import pytest
from pydantic import ValidationError

from app.modules.clinica.schemas import ESTADOS_PIEZA, HallazgoIn, PacienteCreate, PacienteOut


def _paciente() -> dict:
    return {
        "nombre": "Ana Pérez",
        "dni": "30111222",
        "telefono": "1144556677",
    }


def test_paciente_create_extra_forbid() -> None:
    with pytest.raises(ValidationError):
        PacienteCreate(**_paciente(), campo_extra="x")


def test_paciente_create_requiere_nombre_dni_telefono() -> None:
    for clave in ("nombre", "dni", "telefono"):
        datos = _paciente()
        datos.pop(clave)
        with pytest.raises(ValidationError):
            PacienteCreate(**datos)


def test_paciente_out_desde_atributos() -> None:
    assert PacienteOut.model_config.get("from_attributes") is True


def test_hallazgo_estados_validos() -> None:
    assert set(ESTADOS_PIEZA) == {
        "sano",
        "caries",
        "obturacion",
        "corona",
        "extraccion",
        "tratamiento_conducto",
    }
    h = HallazgoIn(estado="tratamiento_conducto")
    assert h.estado == "tratamiento_conducto"


def test_hallazgo_rechaza_conducto_corto() -> None:
    with pytest.raises(ValidationError):
        HallazgoIn(estado="conducto")


def test_hallazgo_extra_forbid_y_fecha_opcional() -> None:
    with pytest.raises(ValidationError):
        HallazgoIn(estado="caries", extra="x")
    h = HallazgoIn(estado="caries")
    assert h.fecha is None
    h2 = HallazgoIn(estado="caries", fecha=date(2026, 11, 4))
    assert h2.fecha == date(2026, 11, 4)
