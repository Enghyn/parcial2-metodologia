"""TDD C-06 grupo 5 — schemas públicos con extra='forbid' (R1)."""
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.public.schemas import PacientePublicoIn, ReservaCreate


def _paciente_valido() -> dict:
    return {"nombre": "Ana Test", "dni": "12345678", "telefono": "1144556677"}


def _reserva_valida() -> dict:
    return {
        "prestacion": "Consulta",
        "duracion_min": 30,
        "inicio": datetime(2027, 7, 1, 9, 0, tzinfo=UTC).isoformat(),
        "profesional_id": str(uuid4()),
        "sillon_id": str(uuid4()),
        "paciente": _paciente_valido(),
    }


def test_paciente_rechaza_campo_extra() -> None:
    with pytest.raises(ValidationError):
        PacientePublicoIn(**_paciente_valido(), extra="no permitido")


def test_paciente_requiere_nombre_dni_telefono() -> None:
    for clave in ("nombre", "dni", "telefono"):
        datos = _paciente_valido()
        datos.pop(clave)
        with pytest.raises(ValidationError):
            PacientePublicoIn(**datos)


def test_reserva_valida_ok() -> None:
    reserva = ReservaCreate(**_reserva_valida())
    assert reserva.duracion_min == 30
    assert reserva.paciente.dni == "12345678"


def test_reserva_rechaza_campo_extra() -> None:
    datos = _reserva_valida()
    datos["foo"] = "bar"
    with pytest.raises(ValidationError):
        ReservaCreate(**datos)


def test_reserva_duracion_no_positiva() -> None:
    datos = _reserva_valida()
    datos["duracion_min"] = 0
    with pytest.raises(ValidationError):
        ReservaCreate(**datos)


def test_reserva_normaliza_inicio_naive_a_art() -> None:
    datos = _reserva_valida()
    datos["inicio"] = "2027-07-01T09:00:00"
    reserva = ReservaCreate(**datos)
    assert reserva.inicio.tzinfo is not None
    assert reserva.inicio.utcoffset() is not None
    assert reserva.inicio.utcoffset().total_seconds() == -3 * 3600
