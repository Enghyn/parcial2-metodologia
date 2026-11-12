"""TDD C-18 tarea 2.3 — `PagoService.confirmar` exige usuario responsable (R4).

Deuda de C-17: la confirmación creaba `MovimientoCaja` con `usuario_id=None`.
Requiere base migrada + seeded (alembic upgrade head + python -m app.db.seed).
"""
from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import registry  # noqa: F401  (registra todas las tablas para las FK)
from app.db.session import get_session_factory
from app.modules.admin.models import Usuario
from app.modules.caja.models import MEDIOS_PAGO, MovimientoCaja
from app.modules.clinica.models import Paciente
from app.modules.pagos.models import IntentoPago, Pago
from app.modules.pagos.service import PagoService
from app.modules.presupuestos.models import Presupuesto

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("db_disponible")]


def _session() -> Session:
    return get_session_factory()()


def _usuario_admin(session: Session) -> Usuario:
    usuario = session.scalar(select(Usuario).where(Usuario.rol == "admin"))
    assert usuario is not None
    return usuario


def _crear_pago(session: Session, *, monto: float = 500.0) -> Pago:
    paciente = session.scalar(select(Paciente).where(Paciente.deleted_at.is_(None)))
    assert paciente is not None
    presupuesto = Presupuesto(paciente_id=paciente.id, estado="aprobado", total=monto)
    session.add(presupuesto)
    session.flush()
    pago = Pago(presupuesto_id=presupuesto.id, monto=monto, estado="pendiente")
    session.add(pago)
    session.commit()
    session.refresh(pago)
    return pago


def _limpiar(session: Session, presupuesto_id: UUID) -> None:
    session.rollback()
    pago_ids = list(session.scalars(select(Pago.id).where(Pago.presupuesto_id == presupuesto_id)))
    if pago_ids:
        session.query(IntentoPago).filter(IntentoPago.pago_id.in_(pago_ids)).delete(
            synchronize_session=False
        )
        session.query(Pago).filter(Pago.presupuesto_id == presupuesto_id).delete(
            synchronize_session=False
        )
    session.query(Presupuesto).filter(Presupuesto.id == presupuesto_id).delete(
        synchronize_session=False
    )
    session.commit()


def _contar_movimientos(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(MovimientoCaja)) or 0


def test_confirmar_exige_usuario_id() -> None:
    session = _session()
    try:
        pago = _crear_pago(session)
        try:
            with pytest.raises(TypeError):
                PagoService(session).confirmar(pago.id)  # type: ignore[call-arg]
        finally:
            _limpiar(session, pago.presupuesto_id)
    finally:
        session.close()


def test_confirmar_crea_movimiento_con_usuario_y_medio_pago_validos() -> None:
    session = _session()
    try:
        pago = _crear_pago(session, monto=500.0)
        usuario = _usuario_admin(session)
        antes = _contar_movimientos(session)
        try:
            resultado = PagoService(session).confirmar(pago.id, usuario.id)
            assert resultado.estado == "aprobado"
            assert resultado.movimiento_id is not None
            assert _contar_movimientos(session) - antes == 1
            movimiento = session.get(MovimientoCaja, resultado.movimiento_id)
            assert movimiento is not None
            assert movimiento.tipo == "ingreso"
            assert movimiento.medio_pago in MEDIOS_PAGO
            assert float(movimiento.monto) == 500.0
            assert movimiento.usuario_id == usuario.id
        finally:
            _limpiar(session, pago.presupuesto_id)
    finally:
        session.close()


def test_confirmar_idempotente_no_duplica_movimiento() -> None:
    session = _session()
    try:
        pago = _crear_pago(session)
        usuario = _usuario_admin(session)
        antes = _contar_movimientos(session)
        try:
            servicio = PagoService(session)
            primero = servicio.confirmar(pago.id, usuario.id)
            segundo = servicio.confirmar(pago.id, usuario.id)
            assert primero.estado == "aprobado"
            assert segundo.estado == "aprobado"
            assert segundo.movimiento_id == primero.movimiento_id
            assert _contar_movimientos(session) - antes == 1
        finally:
            _limpiar(session, pago.presupuesto_id)
    finally:
        session.close()


def test_confirmar_pago_inexistente_value_error() -> None:
    session = _session()
    try:
        usuario = _usuario_admin(session)
        with pytest.raises(ValueError):
            PagoService(session).confirmar(uuid4(), usuario.id)
    finally:
        session.close()
