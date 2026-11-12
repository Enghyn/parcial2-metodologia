"""TDD C-18 tarea 1.1 — schemas públicos del portal (R1 `extra='forbid'`, R9 sin IDs internos).

Capa: unitaria (sin base de datos).
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.public.schemas import (
    AprobacionPublicaIn,
    ItemPresupuestoPublicoOut,
    PagoPublicoOut,
    PresupuestoPublicoOut,
    RechazoPublicoIn,
)

# R9: la superficie pública nunca expone identificadores internos.
IDS_INTERNOS = {"id", "paciente_id", "presupuesto_id", "movimiento_id", "token_publico"}


def _item(**extra: object) -> dict:
    datos = {"descripcion": "Consulta", "cantidad": 2, "arancel": 1000.0, "copago": 100.0}
    datos.update(extra)
    return datos


def test_item_presupuesto_publico_out_valido() -> None:
    item = ItemPresupuestoPublicoOut(**_item())
    assert item.descripcion == "Consulta"
    assert item.cantidad == 2
    assert float(item.arancel) == 1000.0
    assert float(item.copago) == 100.0


def test_item_presupuesto_publico_out_rechaza_extra() -> None:
    with pytest.raises(ValidationError):
        ItemPresupuestoPublicoOut(**_item(extra="no permitido"))


def test_item_presupuesto_publico_out_sin_ids_internos() -> None:
    campos = set(ItemPresupuestoPublicoOut.model_fields)
    assert campos == {"descripcion", "cantidad", "arancel", "copago"}
    assert campos.isdisjoint(IDS_INTERNOS)


def test_presupuesto_publico_out_campos_minimos() -> None:
    presupuesto = PresupuestoPublicoOut(
        estado="enviado", total=1900.0, items=[ItemPresupuestoPublicoOut(**_item())]
    )
    assert set(presupuesto.model_dump()) == {"estado", "total", "items"}
    assert set(presupuesto.model_dump()).isdisjoint(IDS_INTERNOS)
    assert presupuesto.items[0].descripcion == "Consulta"


def test_presupuesto_publico_out_rechaza_extra() -> None:
    with pytest.raises(ValidationError):
        PresupuestoPublicoOut(estado="enviado", total=0.0, items=[], token_publico="x")


def test_pago_publico_out_campos_minimos() -> None:
    pago = PagoPublicoOut(estado="pendiente", monto=500.0, confirmado_en=None)
    assert set(pago.model_dump()) == {"estado", "monto", "confirmado_en"}
    assert set(pago.model_dump()).isdisjoint(IDS_INTERNOS)


def test_pago_publico_out_rechaza_extra() -> None:
    with pytest.raises(ValidationError):
        PagoPublicoOut(estado="pendiente", monto=1.0, confirmado_en=None, movimiento_id="x")


def test_aprobacion_publica_in_exige_firma_no_vacia() -> None:
    assert AprobacionPublicaIn(firma="María López").firma == "María López"
    with pytest.raises(ValidationError):
        AprobacionPublicaIn(firma="")


def test_aprobacion_publica_in_rechaza_extra() -> None:
    with pytest.raises(ValidationError):
        AprobacionPublicaIn(firma="María López", dni="30111222")


def test_rechazo_publico_in_motivo_opcional() -> None:
    assert RechazoPublicoIn().motivo is None
    assert RechazoPublicoIn(motivo="Muy caro").motivo == "Muy caro"


def test_rechazo_publico_in_rechaza_extra() -> None:
    with pytest.raises(ValidationError):
        RechazoPublicoIn(motivo="x", paciente_id="y")
