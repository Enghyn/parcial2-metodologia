"""TDD C-08 — CajaService contra PostgreSQL."""
import logging
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.timezone import TZ_CONSULTORIO
from app.db.session import get_session_factory
from app.modules.admin.models import Usuario
from app.modules.agenda.models import Profesional, Sillon
from app.modules.agenda.schemas import TurnoCreate
from app.modules.agenda.service import TurnoService
from app.modules.caja.models import MovimientoCaja
from app.modules.caja.schemas import MovimientoCreate
from app.modules.caja.service import CajaService
from app.modules.clinica.models import Paciente

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("db_disponible")]


def _session() -> Session:
    return get_session_factory()()


def _usuario(session: Session) -> Usuario:
    usuario = session.scalar(select(Usuario).where(Usuario.rol == "admin"))
    assert usuario is not None
    return usuario


def _fecha_unica() -> date:
    return date(2030, 1, 1) + timedelta(days=uuid4().int % 20000)


def _seed_ids(session: Session) -> dict:
    sillon = session.scalar(
        select(Sillon).where(Sillon.deleted_at.is_(None), Sillon.activo.is_(True))
    )
    profesional = session.scalar(
        select(Profesional).where(Profesional.deleted_at.is_(None), Profesional.activo.is_(True))
    )
    paciente = session.scalar(select(Paciente).where(Paciente.deleted_at.is_(None)))
    assert sillon is not None and profesional is not None and paciente is not None
    return {"sillon": sillon, "profesional": profesional, "paciente": paciente}


def _movimiento(
    session: Session,
    usuario: Usuario,
    fecha: datetime,
    *,
    tipo: str = "ingreso",
    medio: str = "efectivo",
    monto: Decimal = Decimal("100.00"),
    concepto: str = "Test",
) -> MovimientoCaja:
    movimiento = MovimientoCaja(
        tipo=tipo,
        medio_pago=medio,
        monto=monto,
        concepto=concepto,
        usuario_id=usuario.id,
        fecha=fecha,
    )
    session.add(movimiento)
    session.commit()
    session.refresh(movimiento)
    return movimiento


def test_registrar_ingreso_asocia_usuario() -> None:
    session = _session()
    try:
        usuario = _usuario(session)
        movimiento = CajaService(session).registrar(
            MovimientoCreate(
                tipo="ingreso",
                medio_pago="efectivo",
                monto=Decimal("10000.00"),
                concepto="Cobro de consulta",
            ),
            usuario.id,
        )
        assert movimiento.usuario_id == usuario.id
        assert movimiento.tipo == "ingreso"
        assert movimiento.monto == Decimal("10000.00")
    finally:
        session.close()


def test_registrar_turno_borrado_404() -> None:
    session = _session()
    try:
        usuario = _usuario(session)
        ids = _seed_ids(session)
        turno = TurnoService(session).crear(
            TurnoCreate(
                paciente_id=ids["paciente"].id,
                profesional_id=ids["profesional"].id,
                sillon_id=ids["sillon"].id,
                prestacion="Consulta",
                inicio=datetime(2027, 4, 2, 9, 0, tzinfo=TZ_CONSULTORIO),
                duracion_min=30,
            )
        )
        turno.soft_delete()
        session.commit()
        with pytest.raises(HTTPException) as exc:
            CajaService(session).registrar(
                MovimientoCreate(
                    tipo="ingreso",
                    medio_pago="efectivo",
                    monto=Decimal("1000.00"),
                    concepto="Cobro",
                    turno_id=turno.id,
                ),
                usuario.id,
            )
        assert exc.value.status_code == 404
    finally:
        session.close()


def test_listar_por_dia_art() -> None:
    session = _session()
    try:
        usuario = _usuario(session)
        fecha = datetime.combine(_fecha_unica(), time(10, 0), tzinfo=TZ_CONSULTORIO)
        _movimiento(session, usuario, fecha, concepto="Ingreso del día")
        _movimiento(
            session,
            usuario,
            fecha + timedelta(minutes=1),
            tipo="egreso",
            medio="transferencia",
            monto=Decimal("30.00"),
            concepto="Egreso del día",
        )
        movimientos = CajaService(session).listar(fecha.date())
        assert len(movimientos) >= 2
        assert movimientos[0].fecha >= movimientos[-1].fecha
    finally:
        session.close()


def test_resumen_diario() -> None:
    session = _session()
    try:
        usuario = _usuario(session)
        dia = _fecha_unica()
        fecha = datetime.combine(dia, time(10, 0), tzinfo=TZ_CONSULTORIO)
        _movimiento(session, usuario, fecha, monto=Decimal("100.00"))
        _movimiento(session, usuario, fecha, medio="transferencia", monto=Decimal("50.00"))
        _movimiento(
            session,
            usuario,
            fecha,
            tipo="egreso",
            monto=Decimal("30.00"),
            concepto="Insumos",
        )
        resumen = CajaService(session).resumen(dia)
        assert resumen.total_ingresos == Decimal("150.00")
        assert resumen.total_egresos == Decimal("30.00")
        assert resumen.balance == Decimal("120.00")
        assert resumen.por_medio_pago["efectivo"] == Decimal("100.00")
        assert resumen.por_medio_pago["transferencia"] == Decimal("50.00")
    finally:
        session.close()


def test_resumen_vacio() -> None:
    session = _session()
    try:
        resumen = CajaService(session).resumen(_fecha_unica())
        assert resumen.total_ingresos == Decimal("0.00")
        assert resumen.total_egresos == Decimal("0.00")
        assert resumen.balance == Decimal("0.00")
        assert all(valor == Decimal("0.00") for valor in resumen.por_medio_pago.values())
    finally:
        session.close()


def test_contra_asiento_son_dos_filas() -> None:
    session = _session()
    try:
        usuario = _usuario(session)
        fecha = datetime.combine(_fecha_unica(), time(10, 0), tzinfo=TZ_CONSULTORIO)
        original = _movimiento(session, usuario, fecha, monto=Decimal("100.00"))
        contra = _movimiento(
            session,
            usuario,
            fecha,
            tipo="egreso",
            monto=Decimal("100.00"),
            concepto=f"Contra-asiento de {original.id}",
        )
        assert original.id != contra.id
        assert original.tipo == "ingreso"
        assert contra.tipo == "egreso"
    finally:
        session.close()


def test_no_loguea_concepto_clinico(caplog) -> None:
    caplog.set_level(logging.DEBUG)
    session = _session()
    try:
        usuario = _usuario(session)
        CajaService(session).registrar(
            MovimientoCreate(
                tipo="ingreso",
                medio_pago="efectivo",
                monto=Decimal("100.00"),
                concepto="Concepto clínico confidencial",
            ),
            usuario.id,
        )
        propios = [
            registro.getMessage()
            for registro in caplog.records
            if registro.name.startswith("app")
        ]
        assert all("Concepto clínico confidencial" not in mensaje for mensaje in propios)
    finally:
        session.close()
