"""TDD C-12 — schemas de cierre, cuenta corriente y ajuste (R1: extra='forbid')."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.modules.caja.schemas import (
    AjusteCreate,
    AjusteOut,
    CierreCreate,
    CierreOut,
    CuentaCorrienteOut,
    EstadoCierre,
    MovimientoCuentaCorriente,
)


def _uuid() -> UUID:
    return uuid4()


def test_cierre_create_extra_forbid_rechaza_campos_no_declarados() -> None:
    """R1: CierreCreate rechaza campos no declarados (extra='forbid')."""
    with pytest.raises(ValidationError):
        CierreCreate(fecha_dia=date(2030, 1, 1), campo_inexistente="x")


def test_cierre_create_valido_sin_fecha_usa_hoy() -> None:
    """CierreCreate sin fecha_dia es válido (fecha opcional, hoy por defecto)."""
    c = CierreCreate()
    assert c.fecha_dia is None


def test_cierre_create_con_fecha() -> None:
    """CierreCreate con fecha_dia válida."""
    c = CierreCreate(fecha_dia=date(2030, 1, 15))
    assert c.fecha_dia == date(2030, 1, 15)


def test_cierre_out_from_attributes() -> None:
    """CierreOut se construye desde atributos (from_attributes=True)."""
    aprobado = _uuid()
    c = CierreOut(
        id=_uuid(),
        fecha_dia=date(2030, 1, 15),
        estado="cerrado",
        balance=Decimal("12000.50"),
        total_ingresos=Decimal("15000.00"),
        total_egresos=Decimal("3000.00"),
        aprobado_por=aprobado,
        aprobado_en=datetime(2030, 1, 15, 18, 0),
        created_at=datetime(2030, 1, 15, 18, 5),
    )
    assert c.estado == "cerrado"
    assert c.balance == Decimal("12000.50")
    assert c.aprobado_por == aprobado


def test_cierre_estado_solo_valores_permitidos() -> None:
    """EstadoCierre solo permite pendiente/cerrado/reabierto."""
    assert EstadoCierre.__args__ == ("pendiente", "cerrado", "reabierto")  # type: ignore[attr-defined]


def test_cierre_out_extra_forbid() -> None:
    """R1: CierreOut rechaza campos no declarados."""
    with pytest.raises(ValidationError):
        CierreOut(
            id=_uuid(),
            fecha_dia=date(2030, 1, 15),
            estado="cerrado",
            balance=Decimal("0.00"),
            total_ingresos=Decimal("0.00"),
            total_egresos=Decimal("0.00"),
            aprobado_por=None,
            aprobado_en=None,
            created_at=datetime(2030, 1, 15, 18, 0),
            extra_field="no",
        )


def test_cuenta_corriente_out_saldo_y_detalle() -> None:
    """CuentaCorrienteOut tiene saldo y detalle de movimientos."""
    mov = MovimientoCuentaCorriente(
        id=_uuid(),
        fecha=datetime(2030, 1, 15, 10, 0),
        tipo="ingreso",
        medio_pago="efectivo",
        monto=Decimal("5000.00"),
        concepto="Consulta",
        usuario_id=_uuid(),
    )
    cc = CuentaCorrienteOut(
        paciente_id=_uuid(),
        saldo=Decimal("5000.00"),
        detalle=[mov],
    )
    assert cc.saldo == Decimal("5000.00")
    assert len(cc.detalle) == 1
    assert cc.detalle[0].concepto == "Consulta"


def test_cuenta_corriente_out_extra_forbid() -> None:
    """R1: CuentaCorrienteOut rechaza campos no declarados."""
    with pytest.raises(ValidationError):
        CuentaCorrienteOut(
            paciente_id=_uuid(),
            saldo=Decimal("0.00"),
            detalle=[],
            campo_extra="x",
        )


def test_ajuste_create_motivo_vacio_422() -> None:
    """AjusteCreate rechaza motivo vacío (min_length=1)."""
    with pytest.raises(ValidationError):
        AjusteCreate(
            movimiento_corregido_id=_uuid(),
            motivo="",
            tipo="ingreso",
            medio_pago="efectivo",
            monto=Decimal("1000.00"),
            concepto="Ajuste",
        )


def test_ajuste_create_monto_cero_negativo_422() -> None:
    """AjusteCreate rechaza monto <= 0 (gt=0)."""
    with pytest.raises(ValidationError):
        AjusteCreate(
            movimiento_corregido_id=_uuid(),
            motivo="Ajuste",
            tipo="egreso",
            medio_pago="efectivo",
            monto=Decimal("0.00"),
            concepto="Ajuste",
        )


def test_ajuste_create_usuario_aprobador_rechazado_en_body() -> None:
    """R4: usuario_aprobador_id no se acepta en el body (sale del JWT, extra='forbid')."""
    with pytest.raises(ValidationError):
        AjusteCreate(
            movimiento_corregido_id=_uuid(),
            motivo="Ajuste",
            tipo="egreso",
            medio_pago="efectivo",
            monto=Decimal("1000.00"),
            concepto="Ajuste",
            usuario_aprobador_id=_uuid(),  # no debe estar en el body
        )


def test_ajuste_create_valido() -> None:
    """AjusteCreate válido con todos los campos del contra-asiento."""
    a = AjusteCreate(
        movimiento_corregido_id=_uuid(),
        motivo="Corrección de cobro duplicado",
        tipo="egreso",
        medio_pago="efectivo",
        monto=Decimal("15000.00"),
        concepto="Anulación de ingreso",
        turno_id=None,
    )
    assert a.motivo == "Corrección de cobro duplicado"
    assert a.monto == Decimal("15000.00")
    assert a.turno_id is None


def test_ajuste_out_from_attributes() -> None:
    """AjusteOut se construye desde atributos."""
    aprobador = _uuid()
    a = AjusteOut(
        id=_uuid(),
        movimiento_corregido_id=_uuid(),
        movimiento_ajuste_id=_uuid(),
        motivo="Corrección",
        fecha=datetime(2030, 1, 15, 10, 0),
        usuario_aprobador_id=aprobador,
        created_at=datetime(2030, 1, 15, 10, 5),
    )
    assert a.usuario_aprobador_id == aprobador
    assert a.motivo == "Corrección"


def test_ajuste_out_extra_forbid() -> None:
    """R1: AjusteOut rechaza campos no declarados."""
    with pytest.raises(ValidationError):
        AjusteOut(
            id=_uuid(),
            movimiento_corregido_id=_uuid(),
            movimiento_ajuste_id=_uuid(),
            motivo="Corrección",
            fecha=datetime(2030, 1, 15, 10, 0),
            usuario_aprobador_id=_uuid(),
            created_at=datetime(2030, 1, 15, 10, 5),
            campo_inexistente="x",
        )


def test_movimiento_cuenta_corriente_from_attributes() -> None:
    """MovimientoCuentaCorriente desde atributos."""
    m = MovimientoCuentaCorriente(
        id=_uuid(),
        fecha=datetime(2030, 1, 15, 10, 0),
        tipo="egreso",
        medio_pago="transferencia",
        monto=Decimal("3000.00"),
        concepto="Insumos",
        usuario_id=_uuid(),
    )
    assert m.tipo == "egreso"
    assert m.monto == Decimal("3000.00")
