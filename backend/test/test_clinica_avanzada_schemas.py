"""Tests de schemas de ficha clínica avanzada (C-11, R1).

RED: estos tests deben fallar porque los schemas nuevos no existen aún.
"""
from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.clinica.schemas import (
    ConsentimientoCreate,
    ConsentimientoOut,
    EvolucionCreate,
    EvolucionOut,
    HallazgoOut,
)

pytestmark = [pytest.mark.integration]


def test_evolucion_create_rechaza_campo_extra():
    with pytest.raises(ValidationError) as exc:
        EvolucionCreate(
            paciente_id=uuid4(),
            texto="Paciente refiere sensibilidad",
            autor_usuario_id=uuid4(),  # no declarable por el cliente
            fecha=date(2026, 11, 5),   # no declarable por el cliente
            campo_inexistente="no debería aceptar",
        )
    assert "extra" in str(exc.value).lower() or "forbid" in str(exc.value).lower()


def test_evolucion_create_texto_vacio_rechazado():
    with pytest.raises(ValidationError):
        EvolucionCreate(
            paciente_id=uuid4(),
            texto="   ",
        )


def test_evolucion_create_texto_requerido():
    with pytest.raises(ValidationError):
        EvolucionCreate(
            paciente_id=uuid4(),
        )


def test_evolucion_out_acepta_campos():
    out = EvolucionOut(
        id=uuid4(),
        paciente_id=uuid4(),
        autor_usuario_id=uuid4(),
        fecha=date(2026, 11, 5),
        texto="Paciente refiere sensibilidad",
    )
    assert out.texto == "Paciente refiere sensibilidad"
    assert out.paciente_id is not None


def test_consentimiento_create_rechaza_campo_extra():
    with pytest.raises(ValidationError) as exc:
        ConsentimientoCreate(
            paciente_id=uuid4(),
            version="v1",
            campo_inexistente="no debería aceptar",
        )
    assert "extra" in str(exc.value).lower() or "forbid" in str(exc.value).lower()


def test_consentimiento_create_version_vacia_rechazada():
    with pytest.raises(ValidationError):
        ConsentimientoCreate(
            paciente_id=uuid4(),
            version="   ",
        )


def test_consentimiento_create_version_requerida():
    with pytest.raises(ValidationError):
        ConsentimientoCreate(
            paciente_id=uuid4(),
        )


def test_consentimiento_out_acepta_campos():
    out = ConsentimientoOut(
        id=uuid4(),
        paciente_id=uuid4(),
        version="v1",
        fecha=date(2026, 11, 5),
        autor_usuario_id=uuid4(),
    )
    assert out.version == "v1"
    assert out.paciente_id is not None


def test_hallazgo_out_acepta_autor_usuario_id():
    out = HallazgoOut(
        pieza=11,
        estado="caries",
        observacion=None,
        fecha=date(2026, 11, 5),
        autor_usuario_id=uuid4(),
    )
    assert out.autor_usuario_id is not None
