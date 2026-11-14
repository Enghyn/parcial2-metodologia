"""TDD C-21 — schemas de reportes (R1: extra="forbid")."""
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.reportes.schemas import (
    AusentismoOut,
    FacturacionMedioOut,
    FacturacionOSOut,
    FacturacionOut,
    MedioPago,
    OcupacionOut,
    OcupacionRecursoOut,
    ReporteRangoIn,
)


def _rango() -> dict:
    return {"desde": date(2026, 10, 1), "hasta": date(2026, 10, 31)}


def test_rango_extra_forbid() -> None:
    with pytest.raises(ValidationError):
        ReporteRangoIn(**_rango(), campo_inexistente="x")


def test_rango_desde_despues_de_hasta_422() -> None:
    with pytest.raises(ValidationError):
        ReporteRangoIn(desde=date(2026, 11, 1), hasta=date(2026, 10, 1))


def test_rango_desde_igual_a_hasta_valido() -> None:
    r = ReporteRangoIn(desde=date(2026, 10, 5), hasta=date(2026, 10, 5))
    assert r.desde == date(2026, 10, 5)
    assert r.hasta == date(2026, 10, 5)


def test_rango_sin_fechas_valido_defaults_en_service() -> None:
    r = ReporteRangoIn()
    assert r.desde is None and r.hasta is None


def test_rango_con_ids_opcionales() -> None:
    pid = uuid4()
    sid = uuid4()
    r = ReporteRangoIn(**_rango(), profesional_id=pid, sillon_id=sid)
    assert r.profesional_id == pid
    assert r.sillon_id == sid


def test_medio_pago_literal() -> None:
    assert MedioPago.__args__ == ("efectivo", "transferencia", "debito", "credito", "otro")


def test_ocupacion_recurso_extra_forbid() -> None:
    base = {
        "id": uuid4(),
        "nombre": "Sillon 1",
        "reservado": 2,
        "confirmado": 1,
        "presente": 0,
        "atendido": 5,
        "cancelado": 1,
        "tasa_ocupacion": 0.625,
        "horas_bloqueadas": 2.0,
    }
    with pytest.raises(ValidationError):
        OcupacionRecursoOut(**base, campo_extra="no")


def test_ocupacion_out_armado() -> None:
    fila = OcupacionRecursoOut(
        id=uuid4(),
        nombre="Sillon 1",
        reservado=2,
        confirmado=1,
        presente=0,
        atendido=5,
        cancelado=1,
        tasa_ocupacion=0.625,
        horas_bloqueadas=2.0,
    )
    out = OcupacionOut(
        desde=date(2026, 10, 1),
        hasta=date(2026, 10, 31),
        sillones=[fila],
        profesionales=[],
    )
    assert out.desde == date(2026, 10, 1)
    assert len(out.sillones) == 1
    assert out.sillones[0].tasa_ocupacion == 0.625


def test_facturacion_medio_total_no_negativo() -> None:
    m = FacturacionMedioOut(medio_pago="efectivo", total=Decimal("1500.00"))
    assert m.total == Decimal("1500.00")
    with pytest.raises(ValidationError):
        FacturacionMedioOut(medio_pago="efectivo", total=Decimal(-10))


def test_facturacion_os_desglose() -> None:
    os_ = FacturacionOSOut(
        obra_social="OSDE",
        monto_os=Decimal("700.00"),
        copago_paciente=Decimal("300.00"),
        total_paciente=Decimal("1000.00"),
    )
    assert os_.obra_social == "OSDE"
    assert os_.total_paciente == Decimal("1000.00")


def test_facturacion_out_armado() -> None:
    out = FacturacionOut(
        desde=date(2026, 10, 1),
        hasta=date(2026, 10, 31),
        por_medio_pago=[FacturacionMedioOut(medio_pago="efectivo", total=Decimal(1000))],
        total_ingresos=Decimal(1000),
        balance_neto=Decimal(1000),
        por_obra_social=[],
    )
    assert out.total_ingresos == Decimal(1000)
    assert out.balance_neto == Decimal(1000)


def test_ausentismo_tasa_rango_valido() -> None:
    out = AusentismoOut(
        desde=date(2026, 10, 1),
        hasta=date(2026, 10, 31),
        cancelados=2,
        no_presentados=1,
        recuperados=1,
        tasa_ausentismo=0.1,
        total_turnos=30,
    )
    assert out.tasa_ausentismo == 0.1
    assert out.total_turnos == 30


def test_ausentismo_extra_forbid() -> None:
    with pytest.raises(ValidationError):
        AusentismoOut(
            desde=date(2026, 10, 1),
            hasta=date(2026, 10, 31),
            cancelados=0,
            no_presentados=0,
            recuperados=0,
            tasa_ausentismo=0.0,
            total_turnos=0,
            campo_no_permitido="x",
        )
