"""TDD C-21 — ReportesService.ausentismo contra PostgreSQL."""
from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.timezone import TZ_CONSULTORIO
from app.db.session import get_session_factory
from app.modules.agenda.models import Profesional, Sillon, Turno
from app.modules.clinica.models import Paciente
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
    assert sillon is not None and profesional is not None
    return sillon, profesional


def _paciente(session, sufijo: str) -> Paciente:
    p = Paciente(
        nombre=f"Paciente Aus {sufijo}",
        dni=f"98{uuid4().hex[:9]}",
        telefono="01100000000",
        activo=True,
    )
    session.add(p)
    session.commit()
    return p


def _turno(session, *, paciente, profesional, sillon, estado, dia, hora=9):
    inicio = datetime.combine(dia, datetime.min.time().replace(hour=hora), tzinfo=TZ_CONSULTORIO)
    t = Turno(
        paciente_id=paciente.id,
        profesional_id=profesional.id,
        sillon_id=sillon.id,
        prestacion="Consulta",
        inicio=inicio,
        fin=inicio + timedelta(minutes=30),
        duracion_min=30,
        estado=estado,
    )
    session.add(t)
    session.commit()
    return t


def _dia_unico():
    return date(2030, 1, 1) + timedelta(days=uuid4().int % 20000)


def test_ausentismo_con_cancelados_y_no_presentados() -> None:
    session = _session()
    try:
        sillon, profesional = _ids(session)
        paciente = _paciente(session, "a")
        otro = _paciente(session, "b")
        dia = _dia_unico()
        # mismo paciente con 2 turnos: 1 se cuenta como recuperado (heuristica)
        _turno(session, paciente=paciente, profesional=profesional, sillon=sillon, estado="atendido", dia=dia, hora=9)
        _turno(session, paciente=paciente, profesional=profesional, sillon=sillon, estado="cancelado", dia=dia, hora=10)
        _turno(session, paciente=otro, profesional=profesional, sillon=sillon, estado="ausente", dia=dia, hora=11)
        res = ReportesService(session).reporte_ausentismo(dia, dia)
        assert res.cancelados == 1
        assert res.no_presentados == 1
        assert res.recuperados == 1  # paciente con 2 turnos -> N-1
        assert res.total_turnos == 3
        assert res.tasa_ausentismo == round(2 / 3, 4)
    finally:
        session.close()


def test_ausentismo_todo_atendido_tasa_cero() -> None:
    session = _session()
    try:
        sillon, profesional = _ids(session)
        paciente_c = _paciente(session, "c")
        paciente_d = _paciente(session, "d")
        dia = _dia_unico()
        _turno(session, paciente=paciente_c, profesional=profesional, sillon=sillon, estado="atendido", dia=dia)
        _turno(session, paciente=paciente_d, profesional=profesional, sillon=sillon, estado="presente", dia=dia, hora=10)
        res = ReportesService(session).reporte_ausentismo(dia, dia)
        assert res.cancelados == 0
        assert res.no_presentados == 0
        assert res.recuperados == 0  # cada paciente con un turno -> sin reagendados
        assert res.total_turnos == 2
        assert res.tasa_ausentismo == 0.0
    finally:
        session.close()


def test_ausentismo_rango_vacio() -> None:
    session = _session()
    try:
        dia = _dia_unico()
        res = ReportesService(session).reporte_ausentismo(dia, dia)
        assert res.cancelados == 0
        assert res.no_presentados == 0
        assert res.recuperados == 0
        assert res.tasa_ausentismo == 0.0
        assert res.total_turnos == 0
    finally:
        session.close()
