"""Tests de schemas de pre-reserva y reprogramación pública (C-10, R1)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.modules.public.schemas import (
    PreReservaCreate,
    PreReservaOut,
    ReprogramarPublico,
    ReservaCreate,
)

from uuid import uuid4


def _dt() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=1)


def test_pre_reserva_create_acepta_los_cinco_campos():
    obj = PreReservaCreate(
        prestacion="Limpieza",
        duracion_min=30,
        inicio=_dt(),
        profesional_id=uuid4(),
        sillon_id=uuid4(),
    )
    assert obj.duracion_min == 30
    assert obj.pre_reserva_token is None if hasattr(obj, "pre_reserva_token") else True


def test_pre_reserva_create_rechaza_duracion_no_positiva():
    with pytest.raises(ValidationError):
        PreReservaCreate(
            prestacion="Limpieza",
            duracion_min=0,
            inicio=_dt(),
            profesional_id=uuid4(),
            sillon_id=uuid4(),
        )


def test_pre_reserva_create_rechaza_campo_extra():
    with pytest.raises(ValidationError):
        PreReservaCreate(
            prestacion="Limpieza",
            duracion_min=30,
            inicio=_dt(),
            profesional_id=uuid4(),
            sillon_id=uuid4(),
            paciente={"nombre": "x"},  # no permitido
        )


def test_pre_reserva_create_no_acepta_paciente_ni_dni():
    with pytest.raises(ValidationError):
        PreReservaCreate(
            prestacion="Limpieza",
            duracion_min=30,
            inicio=_dt(),
            profesional_id=uuid4(),
            sillon_id=uuid4(),
            dni="123",
        )


def test_reprogramar_publico_solo_inicio():
    obj = ReprogramarPublico(inicio=_dt())
    assert obj.inicio is not None


def test_reprogramar_publico_rechaza_campos_extra():
    with pytest.raises(ValidationError):
        ReprogramarPublico(inicio=_dt(), sillon_id=uuid4())
    with pytest.raises(ValidationError):
        ReprogramarPublico(inicio=_dt(), profesional_id=uuid4())
    with pytest.raises(ValidationError):
        ReprogramarPublico(inicio=_dt(), duracion_min=10)


def test_reserva_create_acepta_pre_reserva_token_opcional():
    obj = ReservaCreate(
        prestacion="Limpieza",
        duracion_min=30,
        inicio=_dt(),
        profesional_id=uuid4(),
        sillon_id=uuid4(),
        paciente={"nombre": "Ana", "dni": "123", "telefono": "555"},
    )
    assert obj.pre_reserva_token is None
    tok = uuid4()
    obj2 = ReservaCreate(
        prestacion="Limpieza",
        duracion_min=30,
        inicio=_dt(),
        profesional_id=uuid4(),
        sillon_id=uuid4(),
        paciente={"nombre": "Ana", "dni": "123", "telefono": "555"},
        pre_reserva_token=tok,
    )
    assert obj2.pre_reserva_token == tok


def test_reserva_create_rechaza_origen():
    with pytest.raises(ValidationError):
        ReservaCreate(
            prestacion="Limpieza",
            duracion_min=30,
            inicio=_dt(),
            profesional_id=uuid4(),
            sillon_id=uuid4(),
            paciente={"nombre": "Ana", "dni": "123", "telefono": "555"},
            origen="publico",
        )
