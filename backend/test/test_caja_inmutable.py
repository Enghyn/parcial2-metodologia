"""Inmutabilidad del libro de caja (R3 / RN-CJ-02)."""
from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.errors import ImmutableLedgerError
from app.db.base import Base, _reject_ledger_delete, _reject_ledger_update
from app.modules.caja.models import MEDIOS_PAGO, TIPOS_MOVIMIENTO, MovimientoCaja


def _movimiento(tipo: str = "ingreso") -> MovimientoCaja:
    return MovimientoCaja(
        tipo=tipo,
        medio_pago="efectivo",
        monto=Decimal("15000.00"),
        concepto="Cobro turno - limpieza",
        usuario_id=uuid4(),
    )


def test_catalogos_de_caja() -> None:
    assert TIPOS_MOVIMIENTO == ("ingreso", "egreso")
    assert MEDIOS_PAGO == ("efectivo", "transferencia", "debito", "credito", "otro")


def test_no_se_puede_actualizar_un_movimiento() -> None:
    with pytest.raises(ImmutableLedgerError):
        _reject_ledger_update(None, None, _movimiento())


def test_no_se_puede_borrar_un_movimiento() -> None:
    with pytest.raises(ImmutableLedgerError):
        _reject_ledger_delete(None, None, _movimiento())


def test_contra_asiento_se_modela_como_movimiento_nuevo() -> None:
    original = _movimiento("ingreso")
    contra = _movimiento("egreso")
    contra.concepto = "Contra-asiento por error de carga"

    assert original.tipo == "ingreso"
    assert contra.tipo == "egreso"
    assert original is not contra
    assert original.monto == contra.monto


def test_movimiento_exige_concepto_y_medio_pago() -> None:
    tabla = Base.metadata.tables["movimientos_caja"]
    assert not tabla.c["concepto"].nullable
    assert not tabla.c["medio_pago"].nullable
