"""TDD C-04 grupo 3 — schemas Pydantic de agenda (R1 extra="forbid")."""
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.agenda.schemas import (
    BloqueoCreate,
    BloqueoOut,
    ReprogramarTurno,
    SobreturnoCreate,
    TurnoCreate,
    TurnoEstadoUpdate,
    TurnoOut,
)


def _now() -> datetime:
    return datetime(2026, 11, 3, 10, 0, tzinfo=UTC)


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
    assert TurnoEstadoUpdate(estado="ausente").estado == "ausente"
    with pytest.raises(ValidationError):
        TurnoEstadoUpdate(estado="no-existe")


def test_turno_create_normaliza_naive_a_art() -> None:
    naive = datetime(2026, 11, 3, 10, 0)  # noqa: DTZ001  (sin tz a propósito)
    t = TurnoCreate(
        paciente_id=uuid4(),
        profesional_id=uuid4(),
        sillon_id=uuid4(),
        prestacion="Consulta",
        inicio=naive,
        duracion_min=30,
    )
    assert t.inicio.tzinfo is not None
    assert t.inicio.utcoffset() == timedelta(hours=-3)
    assert t.inicio.astimezone(UTC).hour == 13


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


def test_reprogramar_turno_normaliza_naive_y_duracion_opcional() -> None:
    datos = ReprogramarTurno(inicio=datetime(2027, 1, 10, 9, 0))  # noqa: DTZ001
    assert datos.duracion_min is None
    assert datos.inicio.utcoffset().total_seconds() == -3 * 3600
    with pytest.raises(ValidationError):
        ReprogramarTurno(inicio=_now(), duracion_min=0)


def test_sobreturno_exige_motivo_y_hereda_turno() -> None:
    datos = {
        "paciente_id": uuid4(),
        "profesional_id": uuid4(),
        "sillon_id": uuid4(),
        "prestacion": "Consulta",
        "inicio": _now(),
        "duracion_min": 30,
        "motivo_sobreturno": "Urgencia",
    }
    sobreturno = SobreturnoCreate(**datos)
    assert sobreturno.motivo_sobreturno == "Urgencia"
    with pytest.raises(ValidationError):
        SobreturnoCreate(**{**datos, "motivo_sobreturno": ""})
    with pytest.raises(ValidationError):
        SobreturnoCreate(**{**datos, "campo_extra": "x"})


def test_turno_out_from_attributes_config() -> None:
    assert TurnoOut.model_config.get("from_attributes") is True


def test_bloqueo_out_from_attributes_config() -> None:
    assert BloqueoOut.model_config.get("from_attributes") is True