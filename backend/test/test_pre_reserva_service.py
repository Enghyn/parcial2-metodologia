"""Integración C-10: servicio de pre-reservas (crear_pre_reserva, slot_libre con retenciones).

Requiere base migrada + seeded (alembic upgrade head + python -m app.db.seed).
"""
from datetime import timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.core.timezone import ahora
from app.db.session import get_session_factory
from app.modules.agenda.models import Bloqueo, Profesional, Sillon, Turno
from app.modules.clinica.models import Paciente
from app.modules.public.models import PreReserva
from app.modules.public.service import PublicReservaService, retencion_vigente, slot_libre

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("db_disponible")]


def _futuro(dias: int = 2):
    return ahora() + timedelta(days=dias)


def _session():
    return get_session_factory()()


def _ids(session):
    sillon = session.scalar(select(Sillon).where(Sillon.deleted_at.is_(None)).order_by(Sillon.nombre))
    prof = session.scalar(
        select(Profesional)
        .where(Profesional.deleted_at.is_(None), Profesional.activo.is_(True))
        .order_by(Profesional.matricula)
    )
    paciente = session.scalar(select(Paciente).where(Paciente.deleted_at.is_(None)))
    assert sillon is not None and prof is not None and paciente is not None
    return sillon, prof, paciente


def _payload(sillon_id, profesional_id, inicio=None, duracion=30, prestacion="Limpieza"):
    if inicio is None:
        inicio = _futuro(2)
    from app.modules.public.schemas import PreReservaCreate

    return PreReservaCreate(
        prestacion=prestacion,
        duracion_min=duracion,
        inicio=inicio,
        profesional_id=profesional_id,
        sillon_id=sillon_id,
    )


def test_crear_pre_reserva_exitosa():
    session = _session()
    try:
        sillon, prof, _paciente = _ids(session)
        servicio = PublicReservaService(session)
        # Buscar un slot libre real usando disponibilidad (fecha lejana)
        from datetime import date

        slots = servicio.disponibilidad(date(2027, 3, 15), 30)
        slot = next(
            (
                s
                for s in slots
                if s.sillon_id == sillon.id and s.profesional_id == prof.id
            ),
            None,
        )
        assert slot is not None, "No hay slot libre para el profesional/sillon en 2027-03-15"
        pr = servicio.crear_pre_reserva(_payload(sillon.id, prof.id, slot.inicio))
        assert pr.id is not None
        assert pr.token is not None
        assert pr.estado == "vigente"
        assert pr.expira_en > ahora()
        assert pr.fin == pr.inicio + timedelta(minutes=30)
        # Limpieza: cancelar la pre-reserva creada
        pr.estado = "cancelada"
        session.commit()
    finally:
        session.close()


def test_crear_pre_reserva_conflicto_con_turno():
    session = _session()
    try:
        sillon, prof, paciente = _ids(session)
        servicio = PublicReservaService(session)
        inicio = _futuro(3)
        turno = Turno(
            paciente_id=paciente.id,
            profesional_id=prof.id,
            sillon_id=sillon.id,
            prestacion="Consulta",
            inicio=inicio,
            fin=inicio + timedelta(minutes=30),
            duracion_min=30,
            estado="reservado",
            origen="interno",
        )
        session.add(turno)
        session.commit()
        try:
            with pytest.raises(HTTPException) as exc:
                servicio.crear_pre_reserva(_payload(sillon.id, prof.id, inicio))
            assert exc.value.status_code == 409
        finally:
            turno.soft_delete()
            session.commit()
    finally:
        session.close()


def test_crear_pre_reserva_conflicto_con_bloqueo():
    session = _session()
    try:
        sillon, prof, _paciente = _ids(session)
        servicio = PublicReservaService(session)
        inicio = _futuro(4)
        bloqueo = Bloqueo(
            sillon_id=sillon.id,
            desde=inicio - timedelta(minutes=30),
            hasta=inicio + timedelta(minutes=30),
            motivo="Test bloqueo",
        )
        session.add(bloqueo)
        session.commit()
        try:
            with pytest.raises(HTTPException) as exc:
                servicio.crear_pre_reserva(_payload(sillon.id, prof.id, inicio))
            assert exc.value.status_code == 409
        finally:
            session.delete(bloqueo)
            session.commit()
    finally:
        session.close()


def test_crear_pre_reserva_inicio_pasado_422():
    session = _session()
    try:
        sillon, prof, _paciente = _ids(session)
        servicio = PublicReservaService(session)
        pasado = ahora() - timedelta(hours=1)
        with pytest.raises(HTTPException) as exc:
            servicio.crear_pre_reserva(_payload(sillon.id, prof.id, pasado))
        assert exc.value.status_code == 422
    finally:
        session.close()


def test_retencion_vigente_pura():
    ahora_dt = ahora()
    futuro = ahora_dt + timedelta(minutes=10)
    vencido = ahora_dt - timedelta(minutes=10)

    class _R:
        def __init__(self, estado, expira_en):
            self.estado = estado
            self.expira_en = expira_en

    assert retencion_vigente(_R("vigente", futuro), ahora_dt) is True
    assert retencion_vigente(_R("vigente", vencido), ahora_dt) is False
    assert retencion_vigente(_R("expirada", futuro), ahora_dt) is False
    assert retencion_vigente(_R("cancelada", futuro), ahora_dt) is False
    assert retencion_vigente(_R("vigente", None), ahora_dt) is True


def test_slot_libre_excluye_retencion_vigente():
    session = _session()
    try:
        sillon, prof, _paciente = _ids(session)
        inicio = _futuro(5)
        # Crear una retención vigente en el mismo hueco
        pr = PreReserva(
            sillon_id=sillon.id,
            profesional_id=prof.id,
            prestacion="Test",
            inicio=inicio,
            fin=inicio + timedelta(minutes=30),
            duracion_min=30,
            expira_en=ahora() + timedelta(minutes=10),
            estado="vigente",
        )
        session.add(pr)
        session.commit()
        try:
            assert (
                slot_libre(
                    [], [], sillon.id, prof.id, inicio, inicio + timedelta(minutes=30), retenciones=[pr]
                )
                is False
            )
            # Retención vencida no bloquea
            pr2 = PreReserva(
                sillon_id=sillon.id,
                profesional_id=prof.id,
                prestacion="Test",
                inicio=inicio,
                fin=inicio + timedelta(minutes=30),
                duracion_min=30,
                expira_en=ahora() - timedelta(minutes=10),
                estado="vigente",
            )
            assert (
                slot_libre(
                    [], [], sillon.id, prof.id, inicio, inicio + timedelta(minutes=30), retenciones=[pr2]
                )
                is True
            )
        finally:
            session.delete(pr)
            session.commit()
    finally:
        session.close()
