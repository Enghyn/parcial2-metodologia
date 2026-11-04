"""TDD C-04 grupo 3 — schemas Pydantic de agenda (R1 extra="forbid")."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.agenda.schemas import (
    BloqueoCreate,
    BloqueoOut,
    TurnoCreate,
    TurnoEstadoUpdate,
    TurnoOut,
)


def _now() -> datetime:
    return datetime(2026, 11, 3, 10, 0, tzinfo=timezone.utc)


def test_turno_create_extra_forbid() -> None:
    with pytest.raises(ValidationError):
        TurnoCreate(
            paciente_id=uuid4(),
            profesional_id=uuid4(),
            sillon_id=uuid4(),
            prestacion="Consulta",
            inicio=_now(),
            duracion_min=30,
            campo_extra="x",
        )


def test_turno_create_campos_requeridos_faltantes() -> None:
    with pytest.raises(ValidationError):
        TurnoCreate(prestacion="Consulta", duracion_min=30)  # type: ignore[call-arg]


def test_turno_create_duracion_no_positiva() -> None:
    with pytest.raises(ValidationError):
        TurnoCreate(
            paciente_id=uuid4(),
            profesional_id=uuid4(),
            sillon_id=uuid4(),
            prestacion="Consulta",
            inicio=_now(),
            duracion_min=0,
        )
    with pytest.raises(ValidationError):
        TurnoCreate(
            paciente_id=uuid4(),
            profesional_id=uuid4(),
            sillon_id=uuid4(),
            prestacion="Consulta",
            inicio=_now(),
            duracion_min=-5,
        )


def test_bloqueo_create_extra_forbid() -> None:
    with pytest.raises(ValidationError):
        BloqueoCreate(
            sillon_id=uuid4(),
            desde=_now(),
            hasta=_now() + timedelta(minutes=30),
            motivo="Limpieza",
            foo="bar",
        )


def test_bloqueo_create_sin_recurso_rechazado() -> None:
    with pytest.raises(ValidationError):
        BloqueoCreate(
            desde=_now(),
            hasta=_now() + timedelta(minutes=30),
            motivo="Limpieza",
        )


def test_bloqueo_create_hasta_menor_o_igual_desde_rechazado() -> None:
    inicio = _now()
    with pytest.raises(ValidationError):
        BloqueoCreate(
            sillon_id=uuid4(),
            desde=inicio,
            hasta=inicio,
            motivo="Limpieza",
        )
    with pytest.raises(ValidationError):
        BloqueoCreate(
            sillon_id=uuid4(),
            desde=inicio,
            hasta=inicio - timedelta(minutes=1),
            motivo="Limpieza",
        )


def test_turno_estado_update_extra_forbid_y_valores() -> None:
    with pytest.raises(ValidationError):
        TurnoEstadoUpdate(estado="reservado", extra="x")
    ok = TurnoEstadoUpdate(estado="cancelado")
    assert ok.estado == "cancelado"
    with pytest.raises(ValidationError):
        TurnoEstadoUpdate(estado="no-existe")


def test_turno_create_normaliza_naive_a_utc() -> None:
    naive = datetime(2026, 11, 3, 10, 0)  # sin tz
    t = TurnoCreate(
        paciente_id=uuid4(),
        profesional_id=uuid4(),
        sillon_id=uuid4(),
        prestacion="Consulta",
        inicio=naive,
        duracion_min=30,
    )
    assert t.inicio.tzinfo is not None


def test_turno_create_sena_monto_default() -> None:
    t = TurnoCreate(
        paciente_id=uuid4(),
        profesional_id=uuid4(),
        sillon_id=uuid4(),
        prestacion="Consulta",
        inicio=_now(),
        duracion_min=30,
    )
    assert t.sena_monto == Decimal("0.00")


def test_turno_out_from_attributes_config() -> None:
    assert TurnoOut.model_config.get("from_attributes") is True


def test_bloqueo_out_from_attributes_config() -> None:
    assert BloqueoOut.model_config.get("from_attributes") is True