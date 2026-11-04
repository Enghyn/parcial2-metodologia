"""TDD C-08 — schemas de caja (R1 y catálogos)."""
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.modules.caja.schemas import MovimientoCreate


def _movimiento() -> dict:
    return {
        "tipo": "ingreso",
        "medio_pago": "efectivo",
        "monto": Decimal("10000.00"),
        "concepto": "Cobro de consulta",
    }


def test_movimiento_extra_forbid() -> None:
    with pytest.raises(ValidationError):
        MovimientoCreate(**_movimiento(), usuario_id="no-permitido")


def test_movimiento_tipo_y_medio_validos() -> None:
    assert MovimientoCreate(**_movimiento()).tipo == "ingreso"
    with pytest.raises(ValidationError):
        MovimientoCreate(**{**_movimiento(), "tipo": "transferencia"})
    with pytest.raises(ValidationError):
        MovimientoCreate(**{**_movimiento(), "medio_pago": "cheque"})


def test_movimiento_monto_positivo() -> None:
    for monto in (Decimal(0), Decimal(-1)):
        with pytest.raises(ValidationError):
            MovimientoCreate(**{**_movimiento(), "monto": monto})


def test_movimiento_concepto_no_vacio() -> None:
    with pytest.raises(ValidationError):
        MovimientoCreate(**{**_movimiento(), "concepto": ""})


def test_movimiento_turno_opcional() -> None:
    assert MovimientoCreate(**_movimiento()).turno_id is None
