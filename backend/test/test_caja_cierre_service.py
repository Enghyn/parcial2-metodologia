"""TDD C-12 — servicio de cierre, cuenta corriente y ajuste (integración PostgreSQL)."""

from __future__ import annotations

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
from app.modules.caja.models import (
    AjusteCaja,
    MovimientoCaja,
)
from app.modules.caja.schemas import AjusteCreate, CierreCreate, MovimientoCreate
from app.modules.caja.service import (
    AjusteService,
    CajaService,
    CierreService,
    CuentaCorrienteService,
)
from app.modules.clinica.models import Paciente

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("db_disponible")]


def _session() -> Session:
    return get_session_factory()()


def _usuario(session: Session, rol: str = "admin") -> Usuario:
    usuario = session.scalar(select(Usuario).where(Usuario.rol == rol, Usuario.activo.is_(True)))
    assert usuario is not None, f"falta usuario seed con rol {rol}"
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


def _crear_turno(
    session: Session, paciente: Paciente, profesional: Profesional, sillon: Sillon
) -> object:
    return TurnoService(session).crear(
        TurnoCreate(
            paciente_id=paciente.id,
            profesional_id=profesional.id,
            sillon_id=sillon.id,
            prestacion="Consulta",
            inicio=datetime(2030, 2, 10, 9, 0, tzinfo=TZ_CONSULTORIO),
            duracion_min=30,
        )
    )


def _movimiento(
    session: Session,
    usuario: Usuario,
    fecha: datetime,
    *,
    tipo: str = "ingreso",
    medio: str = "efectivo",
    monto: Decimal = Decimal("100.00"),
    concepto: str = "Test",
    turno_id: object | None = None,
) -> MovimientoCaja:
    movimiento = MovimientoCaja(
        tipo=tipo,
        medio_pago=medio,
        monto=monto,
        concepto=concepto,
        usuario_id=usuario.id,
        fecha=fecha,
        turno_id=turno_id,
    )
    session.add(movimiento)
    session.commit()
    session.refresh(movimiento)
    return movimiento


def _paciente_baja(session: Session) -> Paciente:
    paciente = session.scalar(select(Paciente).where(Paciente.deleted_at.is_(None)))
    assert paciente is not None
    paciente.soft_delete()
    session.commit()
    return paciente


# --- CierreService ---

def test_cerrar_dia_con_movimientos_201() -> None:
    """Admin cierra un día con movimientos: se crea CierreCaja con balance calculado."""
    session = _session()
    try:
        usuario = _usuario(session, "admin")
        ids = _seed_ids(session)
        turno = _crear_turno(session, ids["paciente"], ids["profesional"], ids["sillon"])
        dia = _fecha_unica()
        fecha = datetime.combine(dia, time(10, 0), tzinfo=TZ_CONSULTORIO)
        _movimiento(session, usuario, fecha, monto=Decimal("10000.00"), concepto="Consulta", turno_id=turno.id)
        _movimiento(
            session, usuario, fecha, tipo="egreso", monto=Decimal("2000.00"), concepto="Insumos"
        )

        cierre = CierreService(session).cerrar(CierreCreate(fecha_dia=dia), usuario.id)
        assert cierre.estado == "cerrado"
        assert cierre.balance == Decimal("8000.00")
        assert cierre.total_ingresos == Decimal("10000.00")
        assert cierre.total_egresos == Decimal("2000.00")
        assert cierre.aprobado_por == usuario.id
        assert cierre.aprobado_en is not None
        assert cierre.fecha_dia == dia
    finally:
        session.close()


def test_cerrar_dia_sin_movimientos_balance_cero() -> None:
    """TRIANGULATE: cerrar día sin movimientos tiene balance cero."""
    session = _session()
    try:
        usuario = _usuario(session, "admin")
        dia = _fecha_unica()
        cierre = CierreService(session).cerrar(CierreCreate(fecha_dia=dia), usuario.id)
        assert cierre.balance == Decimal("0.00")
        assert cierre.total_ingresos == Decimal("0.00")
        assert cierre.total_egresos == Decimal("0.00")
        assert cierre.estado == "cerrado"
    finally:
        session.close()


def test_cerrar_dia_ya_cerrado_409() -> None:
    """Día ya cerrado: segundo cierre responde 409."""
    session = _session()
    try:
        usuario = _usuario(session, "admin")
        dia = _fecha_unica()
        CierreService(session).cerrar(CierreCreate(fecha_dia=dia), usuario.id)
        with pytest.raises(HTTPException) as exc:
            CierreService(session).cerrar(CierreCreate(fecha_dia=dia), usuario.id)
        assert exc.value.status_code == 409
    finally:
        session.close()


def test_listar_cierres() -> None:
    """GET /cierres lista cierres existentes."""
    session = _session()
    try:
        usuario = _usuario(session, "admin")
        dia = _fecha_unica()
        CierreService(session).cerrar(CierreCreate(fecha_dia=dia), usuario.id)
        cierres = CierreService(session).listar()
        assert any(c.fecha_dia == dia and c.estado == "cerrado" for c in cierres)
    finally:
        session.close()


# --- Registrar bloqueado por día cerrado ---

def test_registrar_rechazado_en_dia_cerrado_409() -> None:
    """registrar rechaza movimiento en día con cierre aprobado (409, no persiste)."""
    session = _session()
    try:
        usuario = _usuario(session, "recepcion")
        dia = _fecha_unica()
        # Cerrar el día como admin
        admin = _usuario(session, "admin")
        CierreService(session).cerrar(CierreCreate(fecha_dia=dia), admin.id)

        with pytest.raises(HTTPException) as exc:
            CajaService(session).registrar(
                MovimientoCreate(
                    tipo="ingreso",
                    medio_pago="efectivo",
                    monto=Decimal("1000.00"),
                    concepto="Después del cierre",
                ),
                usuario.id,
            )
        assert exc.value.status_code == 409

        # Verificar que no se persistió el movimiento
        movimientos = session.scalars(
            select(MovimientoCaja).where(MovimientoCaja.concepto == "Después del cierre")
        ).all()
        assert len(movimientos) == 0
    finally:
        session.close()


# --- Cuenta corriente ---

def test_saldo_derivado_de_movimientos() -> None:
    """Saldo = suma(ingresos) - suma(egresos) de movimientos vinculados a turnos del paciente."""
    session = _session()
    try:
        usuario = _usuario(session, "admin")
        ids = _seed_ids(session)
        turno = _crear_turno(session, ids["paciente"], ids["profesional"], ids["sillon"])
        fecha = datetime(2030, 2, 10, 10, 0, tzinfo=TZ_CONSULTORIO)
        _movimiento(session, usuario, fecha, monto=Decimal("5000.00"), concepto="Consulta", turno_id=turno.id)
        _movimiento(
            session, usuario, fecha, tipo="egreso", monto=Decimal("1000.00"), concepto="Descuento", turno_id=turno.id
        )

        saldo = CuentaCorrienteService(session).saldo(ids["paciente"].id)
        assert saldo == Decimal("4000.00")

        detalle = CuentaCorrienteService(session).detalle(ids["paciente"].id)
        assert len(detalle) == 2
    finally:
        session.close()


def test_saldo_cero_paciente_sin_movimientos() -> None:
    """TRIANGULATE: paciente sin movimientos tiene saldo 0 y detalle vacío."""
    session = _session()
    try:
        ids = _seed_ids(session)
        saldo = CuentaCorrienteService(session).saldo(ids["paciente"].id)
        assert saldo == Decimal("0.00")
        detalle = CuentaCorrienteService(session).detalle(ids["paciente"].id)
        assert detalle == []
    finally:
        session.close()


def test_paciente_baja_404() -> None:
    """Paciente dado de baja (deleted_at no nulo) responde 404."""
    session = _session()
    try:
        paciente = _paciente_baja(session)
        with pytest.raises(HTTPException) as exc:
            CuentaCorrienteService(session).saldo(paciente.id)
        assert exc.value.status_code == 404
    finally:
        session.close()


# --- Ajustes ---

def test_ajuste_admin_crea_contra_asiento_y_fila() -> None:
    """Admin registra ajuste: crea contra-asiento en movimientos_caja + fila en ajustes_caja."""
    session = _session()
    try:
        usuario = _usuario(session, "admin")
        ids = _seed_ids(session)
        turno = _crear_turno(session, ids["paciente"], ids["profesional"], ids["sillon"])
        fecha = datetime(2030, 2, 10, 11, 0, tzinfo=TZ_CONSULTORIO)
        original = _movimiento(
            session, usuario, fecha, monto=Decimal("10000.00"), concepto="Cobro original", turno_id=turno.id
        )

        ajuste = AjusteService(session).registrar(
            AjusteCreate(
                movimiento_corregido_id=original.id,
                motivo="Corrección de monto",
                tipo="egreso",
                medio_pago="efectivo",
                monto=Decimal("10000.00"),
                concepto="Anulación de cobro",
                turno_id=turno.id,
            ),
            usuario.id,
        )

        # Verificar contra-asiento existe
        contra = session.scalar(
            select(MovimientoCaja).where(MovimientoCaja.id == ajuste.movimiento_ajuste_id)
        )
        assert contra is not None
        assert contra.tipo == "egreso"
        assert contra.monto == Decimal("10000.00")

        # Verificar fila en ajustes_caja
        ajuste_row = session.scalar(
            select(AjusteCaja).where(AjusteCaja.id == ajuste.id)
        )
        assert ajuste_row is not None
        assert ajuste_row.movimiento_corregido_id == original.id
        assert ajuste_row.movimiento_ajuste_id == contra.id
        assert ajuste_row.motivo == "Corrección de monto"
        assert ajuste_row.usuario_aprobador_id == usuario.id

        # Verificar que el original sigue intacto
        original_row = session.scalar(
            select(MovimientoCaja).where(MovimientoCaja.id == original.id)
        )
        assert original_row.tipo == "ingreso"
        assert original_row.monto == Decimal("10000.00")
    finally:
        session.close()


def test_ajuste_recepcion_403() -> None:
    """Recepción no puede registrar ajuste (403)."""
    session = _session()
    try:
        usuario = _usuario(session, "recepcion")
        with pytest.raises(HTTPException) as exc:
            AjusteService(session).registrar(
                AjusteCreate(
                    movimiento_corregido_id=uuid4(),
                    motivo="Intento no autorizado",
                    tipo="egreso",
                    medio_pago="efectivo",
                    monto=Decimal("100.00"),
                    concepto="No debe crearse",
                ),
                usuario.id,
            )
        assert exc.value.status_code == 403
    finally:
        session.close()


def test_ajuste_motivo_largo_limite() -> None:
    """TRIANGULATE: ajuste con motivo en el límite de 255 caracteres."""
    session = _session()
    try:
        usuario = _usuario(session, "admin")
        motivo = "x" * 255
        ajuste = AjusteService(session).registrar(
            AjusteCreate(
                movimiento_corregido_id=uuid4(),
                motivo=motivo,
                tipo="egreso",
                medio_pago="efectivo",
                monto=Decimal("1.00"),
                concepto="Límite",
            ),
            usuario.id,
        )
        assert ajuste.motivo == motivo
    finally:
        session.close()
