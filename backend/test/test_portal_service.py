"""TDD C-18 tareas 2.1 y 2.2 — `PortalPublicoService` contra Postgres (integración).

Requiere base migrada + seeded (alembic upgrade head + python -m app.db.seed).
"""
from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import registry  # noqa: F401  (registra todas las tablas para las FK)
from app.db.session import get_session_factory
from app.modules.admin.models import Usuario
from app.modules.caja.models import MEDIOS_PAGO, MovimientoCaja
from app.modules.clinica.models import Paciente
from app.modules.pagos.models import IntentoPago, Pago
from app.modules.presupuestos.models import ItemPresupuesto, Presupuesto
from app.modules.public import portal_service
from app.modules.public.portal_service import PortalPublicoService

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("db_disponible")]


def _session() -> Session:
    return get_session_factory()()


def _crear_presupuesto(
    session: Session,
    *,
    estado: str = "enviado",
    items: list[tuple[str, int, float, float]] | None = None,
    aprobado_en=None,
) -> Presupuesto:
    paciente = session.scalar(select(Paciente).where(Paciente.deleted_at.is_(None)))
    assert paciente is not None
    p = Presupuesto(paciente_id=paciente.id, estado=estado, total=0.0, aprobado_en=aprobado_en)
    session.add(p)
    session.flush()
    total = 0.0
    for descripcion, cantidad, arancel, copago in (
        items if items is not None else [("Consulta", 2, 1000.0, 100.0)]
    ):
        session.add(
            ItemPresupuesto(
                presupuesto_id=p.id,
                descripcion=descripcion,
                cantidad=cantidad,
                arancel=arancel,
                copago=copago,
            )
        )
        total += arancel * cantidad - copago
    p.total = total
    session.commit()
    session.refresh(p)
    return p


def _limpiar(session: Session, presupuesto_id: UUID) -> None:
    """Borra el presupuesto y sus dependencias mutables (MovimientoCaja es append-only)."""
    session.rollback()  # descarta cualquier transacción fallida pendiente
    pago_ids = list(
        session.scalars(select(Pago.id).where(Pago.presupuesto_id == presupuesto_id))
    )
    if pago_ids:
        session.query(IntentoPago).filter(IntentoPago.pago_id.in_(pago_ids)).delete(
            synchronize_session=False
        )
        session.query(Pago).filter(Pago.presupuesto_id == presupuesto_id).delete(
            synchronize_session=False
        )
    session.query(ItemPresupuesto).filter(
        ItemPresupuesto.presupuesto_id == presupuesto_id
    ).delete(synchronize_session=False)
    session.query(Presupuesto).filter(Presupuesto.id == presupuesto_id).delete(
        synchronize_session=False
    )
    session.commit()


# --- Tarea 2.1: lectura y firma simple del presupuesto ---


def test_obtener_presupuesto_publico_devuelve_items_total_y_estado() -> None:
    session = _session()
    try:
        p = _crear_presupuesto(session)
        try:
            out = PortalPublicoService(session).obtener_presupuesto_publico(p.token_publico)
            assert out.estado == "enviado"
            assert float(out.total) == 1900.0
            assert len(out.items) == 1
            assert out.items[0].descripcion == "Consulta"
            assert out.items[0].cantidad == 2
            assert float(out.items[0].arancel) == 1000.0
            assert float(out.items[0].copago) == 100.0
            assert not hasattr(out, "id")
            assert not hasattr(out, "paciente_id")
        finally:
            _limpiar(session, p.id)
    finally:
        session.close()


def test_obtener_presupuesto_token_inexistente_404() -> None:
    session = _session()
    try:
        with pytest.raises(HTTPException) as exc:
            PortalPublicoService(session).obtener_presupuesto_publico(uuid4())
        assert exc.value.status_code == 404
    finally:
        session.close()


def test_aprobar_enviado_pasa_a_aprobado_y_registra_fecha() -> None:
    session = _session()
    try:
        p = _crear_presupuesto(session, estado="enviado")
        try:
            out = PortalPublicoService(session).aprobar(p.token_publico, "María López")
            assert out.estado == "aprobado"
            session.refresh(p)
            assert p.estado == "aprobado"
            assert p.aprobado_en is not None
        finally:
            _limpiar(session, p.id)
    finally:
        session.close()


def test_aprobar_ya_aprobado_es_idempotente() -> None:
    from app.core.timezone import ahora

    session = _session()
    try:
        original = ahora()
        p = _crear_presupuesto(session, estado="aprobado", aprobado_en=original)
        try:
            out = PortalPublicoService(session).aprobar(p.token_publico, "Otra firma")
            assert out.estado == "aprobado"
            session.refresh(p)
            assert p.aprobado_en == original  # no genera efectos adicionales
        finally:
            _limpiar(session, p.id)
    finally:
        session.close()


def test_aprobar_presupuesto_cobrado_409() -> None:
    session = _session()
    try:
        p = _crear_presupuesto(session, estado="cobrado")
        try:
            with pytest.raises(HTTPException) as exc:
                PortalPublicoService(session).aprobar(p.token_publico, "María López")
            assert exc.value.status_code == 409
        finally:
            _limpiar(session, p.id)
    finally:
        session.close()


def test_aprobar_token_inexistente_404() -> None:
    session = _session()
    try:
        with pytest.raises(HTTPException) as exc:
            PortalPublicoService(session).aprobar(uuid4(), "María López")
        assert exc.value.status_code == 404
    finally:
        session.close()


def test_rechazar_enviado_pasa_a_rechazado() -> None:
    session = _session()
    try:
        p = _crear_presupuesto(session, estado="enviado")
        try:
            out = PortalPublicoService(session).rechazar(p.token_publico, "Muy caro")
            assert out.estado == "rechazado"
            session.refresh(p)
            assert p.estado == "rechazado"
        finally:
            _limpiar(session, p.id)
    finally:
        session.close()


def test_rechazar_presupuesto_cobrado_409() -> None:
    session = _session()
    try:
        p = _crear_presupuesto(session, estado="cobrado")
        try:
            with pytest.raises(HTTPException) as exc:
                PortalPublicoService(session).rechazar(p.token_publico, None)
            assert exc.value.status_code == 409
        finally:
            _limpiar(session, p.id)
    finally:
        session.close()


def test_rechazar_token_inexistente_404() -> None:
    session = _session()
    try:
        with pytest.raises(HTTPException) as exc:
            PortalPublicoService(session).rechazar(uuid4(), None)
        assert exc.value.status_code == 404
    finally:
        session.close()


# --- Tarea 2.2: confirmación pública del pago (D3/D4) ---


def _contar_movimientos(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(MovimientoCaja)) or 0


def _pago_del_presupuesto(session: Session, presupuesto_id: UUID) -> Pago | None:
    return session.scalar(
        select(Pago).where(Pago.presupuesto_id == presupuesto_id).order_by(Pago.created_at.desc())
    )


def _usuario_portal(session: Session) -> Usuario:
    usuario = session.scalar(
        select(Usuario).where(Usuario.email == get_settings().portal_usuario_email)
    )
    assert usuario is not None
    return usuario


def test_confirmar_pago_publico_crea_un_movimiento_y_aprueba() -> None:
    session = _session()
    try:
        p = _crear_presupuesto(session, estado="aprobado")
        usuario = _usuario_portal(session)
        antes = _contar_movimientos(session)
        try:
            out = PortalPublicoService(session).confirmar_pago_publico(p.token_publico)
            assert out.estado == "aprobado"
            assert float(out.monto) == 1900.0
            assert out.confirmado_en is not None
            assert not hasattr(out, "id")
            assert not hasattr(out, "presupuesto_id")
            assert not hasattr(out, "movimiento_id")

            assert _contar_movimientos(session) - antes == 1
            pago = _pago_del_presupuesto(session, p.id)
            assert pago is not None
            assert pago.estado == "aprobado"
            assert pago.movimiento_id is not None
            movimiento = session.get(MovimientoCaja, pago.movimiento_id)
            assert movimiento is not None
            assert movimiento.tipo == "ingreso"
            assert movimiento.medio_pago in MEDIOS_PAGO
            assert float(movimiento.monto) == 1900.0
            assert movimiento.usuario_id == usuario.id
        finally:
            _limpiar(session, p.id)
    finally:
        session.close()


def test_confirmar_pago_publico_doble_confirmacion_un_solo_movimiento() -> None:
    session = _session()
    try:
        p = _crear_presupuesto(session, estado="aprobado")
        antes = _contar_movimientos(session)
        try:
            servicio = PortalPublicoService(session)
            primero = servicio.confirmar_pago_publico(p.token_publico)
            segundo = servicio.confirmar_pago_publico(p.token_publico)
            assert primero.estado == "aprobado"
            assert segundo.estado == "aprobado"
            assert float(segundo.monto) == float(primero.monto)
            assert _contar_movimientos(session) - antes == 1
        finally:
            _limpiar(session, p.id)
    finally:
        session.close()


def test_confirmar_pago_publico_concurrente_un_solo_movimiento() -> None:
    session = _session()
    try:
        p = _crear_presupuesto(session, estado="aprobado")
        antes = _contar_movimientos(session)
        barrera = threading.Barrier(2)
        resultados: list = []
        errores: list = []

        def _confirmar() -> None:
            s = _session()
            try:
                barrera.wait(timeout=10)
                resultados.append(PortalPublicoService(s).confirmar_pago_publico(p.token_publico))
            except Exception as exc:  # noqa: BLE001 (se reporta en el assert)
                errores.append(exc)
            finally:
                s.close()

        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                futuros = [pool.submit(_confirmar) for _ in range(2)]
                for futuro in futuros:
                    futuro.result(timeout=30)
            assert errores == []
            assert len(resultados) == 2
            assert all(r.estado == "aprobado" for r in resultados)
            assert _contar_movimientos(session) - antes == 1
            pagos = list(session.scalars(select(Pago).where(Pago.presupuesto_id == p.id)))
            assert len(pagos) == 1
            assert pagos[0].estado == "aprobado"
            intentos = session.scalar(
                select(func.count())
                .select_from(IntentoPago)
                .where(IntentoPago.pago_id == pagos[0].id)
            )
            assert intentos == 1
        finally:
            _limpiar(session, p.id)
    finally:
        session.close()


def test_confirmar_pago_publico_no_aprobado_409() -> None:
    session = _session()
    try:
        p = _crear_presupuesto(session, estado="enviado")
        antes = _contar_movimientos(session)
        try:
            with pytest.raises(HTTPException) as exc:
                PortalPublicoService(session).confirmar_pago_publico(p.token_publico)
            assert exc.value.status_code == 409
            assert _contar_movimientos(session) - antes == 0
        finally:
            _limpiar(session, p.id)
    finally:
        session.close()


def test_confirmar_pago_publico_token_inexistente_404() -> None:
    session = _session()
    try:
        with pytest.raises(HTTPException) as exc:
            PortalPublicoService(session).confirmar_pago_publico(uuid4())
        assert exc.value.status_code == 404
    finally:
        session.close()


def test_confirmar_pago_publico_usuario_portal_inexistente_409(monkeypatch) -> None:
    session = _session()
    try:
        p = _crear_presupuesto(session, estado="aprobado")
        antes = _contar_movimientos(session)
        monkeypatch.setattr(
            portal_service,
            "get_settings",
            lambda: get_settings().model_copy(
                update={"portal_usuario_email": "nadie@consultorio.test"}
            ),
        )
        try:
            with pytest.raises(HTTPException) as exc:
                PortalPublicoService(session).confirmar_pago_publico(p.token_publico)
            assert exc.value.status_code == 409
            assert _contar_movimientos(session) - antes == 0
            assert _pago_del_presupuesto(session, p.id) is None
        finally:
            _limpiar(session, p.id)
    finally:
        session.close()


def test_confirmar_pago_publico_reutiliza_pago_pendiente() -> None:
    session = _session()
    try:
        p = _crear_presupuesto(session, estado="aprobado")
        pendiente = Pago(presupuesto_id=p.id, monto=1900.0, estado="pendiente")
        session.add(pendiente)
        session.commit()
        session.refresh(pendiente)
        antes = _contar_movimientos(session)
        try:
            out = PortalPublicoService(session).confirmar_pago_publico(p.token_publico)
            assert out.estado == "aprobado"
            assert _contar_movimientos(session) - antes == 1
            pagos = list(session.scalars(select(Pago).where(Pago.presupuesto_id == p.id)))
            assert len(pagos) == 1
            assert pagos[0].id == pendiente.id
        finally:
            _limpiar(session, p.id)
    finally:
        session.close()


def test_obtener_pago_publico_pendiente_sintetizado_sin_crear_fila() -> None:
    session = _session()
    try:
        p = _crear_presupuesto(session, estado="aprobado")
        try:
            out = PortalPublicoService(session).obtener_pago_publico(p.token_publico)
            assert out.estado == "pendiente"
            assert float(out.monto) == 1900.0
            assert out.confirmado_en is None
            assert _pago_del_presupuesto(session, p.id) is None
        finally:
            _limpiar(session, p.id)
    finally:
        session.close()


def test_obtener_pago_publico_aprobado_tras_confirmar() -> None:
    session = _session()
    try:
        p = _crear_presupuesto(session, estado="aprobado")
        try:
            servicio = PortalPublicoService(session)
            servicio.confirmar_pago_publico(p.token_publico)
            out = servicio.obtener_pago_publico(p.token_publico)
            assert out.estado == "aprobado"
            assert float(out.monto) == 1900.0
            assert out.confirmado_en is not None
        finally:
            _limpiar(session, p.id)
    finally:
        session.close()


def test_obtener_pago_publico_no_aprobado_409() -> None:
    session = _session()
    try:
        p = _crear_presupuesto(session, estado="enviado")
        try:
            with pytest.raises(HTTPException) as exc:
                PortalPublicoService(session).obtener_pago_publico(p.token_publico)
            assert exc.value.status_code == 409
        finally:
            _limpiar(session, p.id)
    finally:
        session.close()


def test_obtener_pago_publico_token_inexistente_404() -> None:
    session = _session()
    try:
        with pytest.raises(HTTPException) as exc:
            PortalPublicoService(session).obtener_pago_publico(uuid4())
        assert exc.value.status_code == 404
    finally:
        session.close()
