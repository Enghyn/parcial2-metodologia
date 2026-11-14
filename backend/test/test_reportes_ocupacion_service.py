"""TDD C-21 — ReportesService.ocupacion contra PostgreSQL."""
from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.timezone import TZ_CONSULTORIO
from app.db.session import get_session_factory
from app.modules.agenda.models import Profesional, Sillon, Turno
from app.modules.clinica.models import Paciente
from app.modules.reportes.schemas import OcupacionOut
from app.modules.reportes.service import ReportesService

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("db_disponible")]


def _session():
    return get_session_factory()()


def _ids(session):
    sillon = session.scalar(
        select(Sillon).where(Sillon.deleted_at.is_(None), Sillon.activo.is_(True))
    )
    profesional = session.scalar(
        select(Profesional).where(Profesional.deleted_at.is_(None), Profesional.activo.is_(True))
    )
    paciente = session.scalar(select(Paciente).where(Paciente.deleted_at.is_(None)))
    assert sillon is not None and profesional is not None and paciente is not None
    return sillon, profesional, paciente


def _turno(session, *, paciente, profesional, sillon, estado, dia, hora=9, dur=30):
    inicio = datetime.combine(dia, datetime.min.time().replace(hour=hora), tzinfo=TZ_CONSULTORIO)
    t = Turno(
        paciente_id=paciente.id,
        profesional_id=profesional.id,
        sillon_id=sillon.id,
        prestacion="Consulta",
        inicio=inicio,
        fin=inicio + timedelta(minutes=dur),
        duracion_min=dur,
        estado=estado,
    )
    session.add(t)
    session.commit()
    return t


def _dia_unico():
    return date(2030, 1, 1) + timedelta(days=uuid4().int % 20000)


def test_ocupacion_por_sillon_con_turnos() -> None:
    session = _session()
    try:
        sillon, profesional, paciente = _ids(session)
        dia = _dia_unico()
        _turno(session, paciente=paciente, profesional=profesional, sillon=sillon, estado="atendido", dia=dia)
        _turno(session, paciente=paciente, profesional=profesional, sillon=sillon, estado="atendido", dia=dia)
        _turno(session, paciente=paciente, profesional=profesional, sillon=sillon, estado="cancelado", dia=dia)
        res = ReportesService(session).reporte_ocupacion(dia, dia, sillon_id=sillon.id)
        assert isinstance(res, OcupacionOut)
        filas = {f.nombre: f for f in res.sillones}
        assert sillon.nombre in filas
        f = filas[sillon.nombre]
        assert f.atendido == 2
        assert f.cancelado == 1
        assert f.reservado == 0
        assert f.tasa_ocupacion == 1.0  # 2 atendidos / 2 totales denominador
    finally:
        session.close()


def test_ocupacion_rango_vacio_tasas_cero() -> None:
    session = _session()
    try:
        _sillon, _profesional, _paciente = _ids(session)
        dia = _dia_unico()
        res = ReportesService(session).reporte_ocupacion(dia, dia)
        assert res.sillones == []
        assert res.profesionales == []
        assert res.desde == dia
        assert res.hasta == dia
    finally:
        session.close()


def test_ocupacion_filtro_por_profesional() -> None:
    session = _session()
    try:
        sillon, profesional, paciente = _ids(session)
        otro = session.scalar(
            select(Profesional).where(
                Profesional.id != profesional.id,
                Profesional.deleted_at.is_(None),
                Profesional.activo.is_(True),
            )
        )
        if otro is None:
            # Crear un profesional extra si no hay segundo activo
            from app.modules.admin.models import Usuario

            usuario = session.scalar(select(Usuario).where(Usuario.rol == "odontologo"))
            assert usuario is not None
            otro = Profesional(
                usuario_id=usuario.id,
                nombre="Otro Profesional",
                matricula="MP-999",
                especialidad="General",
                duracion_default_min=30,
                activo=True,
            )
            session.add(otro)
            session.commit()
        dia = _dia_unico()
        _turno(session, paciente=paciente, profesional=profesional, sillon=sillon, estado="atendido", dia=dia)
        _turno(session, paciente=paciente, profesional=otro, sillon=sillon, estado="cancelado", dia=dia)
        res = ReportesService(session).reporte_ocupacion(dia, dia, profesional_id=profesional.id)
        profs = {f.id: f for f in res.profesionales}
        assert profesional.id in profs
        assert profs[profesional.id].atendido == 1
        assert profs[profesional.id].cancelado == 0
        assert otro.id not in profs
    finally:
        session.close()
