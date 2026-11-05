"""Tests de `origen` en Turno (C-10, D3). Parte pura (schemas + firma)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.agenda.schemas import TurnoCreate, TurnoOut
from app.modules.agenda.service import TurnoService


def _inicio() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=1)


def test_turno_create_rechaza_origen():
    with pytest.raises(ValidationError):
        TurnoCreate(
            prestacion="Limpieza",
            duracion_min=30,
            inicio=_inicio(),
            profesional_id=uuid4(),
            sillon_id=uuid4(),
            origen="publico",
        )


def test_turno_out_incluye_origen():
    assert "origen" in TurnoOut.model_fields


def test_turno_service_crear_tiene_parametro_origen_keyword_only():
    import inspect

    sig = inspect.signature(TurnoService.crear)
    assert "origen" in sig.parameters
    assert sig.parameters["origen"].default == "interno"
    # keyword-only
    assert sig.parameters["origen"].kind == inspect.Parameter.KEYWORD_ONLY


def test_turno_service_crear_sobreturno_tiene_origen():
    import inspect

    sig = inspect.signature(TurnoService.crear_sobreturno)
    assert "origen" in sig.parameters
