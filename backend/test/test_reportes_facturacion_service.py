"""TDD C-21 — ReportesService.facturacion contra PostgreSQL."""
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.timezone import TZ_CONSULTORIO
from app.db.session import get_session_factory
from app.modules.admin.models import Usuario
from app.modules.agenda.models import Profesional, Sillon, Turno
from app.modules.caja.models import MovimientoCaja
from app.modules.clinica.models import Paciente
from app.modules.os.models import Convenio, ObraSocial, PacienteObraSocial
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
        nombre=f"Paciente Test {sufijo}",
        dni=f"99{int(uuid4()) % 100000000:08d}",
        telefono="01100000000",
        activo=True,
    )
    session.add(p)
    session.commit()
    return p


def _turno(session, *, paciente, profesional, sillon, dia, hora=9):
    inicio = datetime.combine(dia, datetime.min.time().replace(hour=hora), tzinfo=TZ_CONSULTORIO)
    t = Turno(
        paciente_id=paciente.id,
        profesional_id=profesional.id,
        sillon_id=sillon.id,
        prestacion="Consulta",
        inicio=inicio,
        fin=inicio + timedelta(minutes=30),
        duracion_min=30,
        estado="atendido",
    )
    session.add(t)
    session.flush()
    return t


def _movimiento(session, *, usuario, turno, medio_pago, monto, dia, hora=10):
    fecha = datetime.combine(dia, datetime.min.time().replace(hour=hora), tzinfo=TZ_CONSULTORIO)
    m = MovimientoCaja(
        tipo="ingreso",
        medio_pago=medio_pago,
        monto=monto,
        concepto="Cobro consulta",
        turno_id=turno.id,
        usuario_id=usuario.id,
        fecha=fecha,
    )
    session.add(m)
    session.commit()
    return m


def _usuario(session):
    return session.scalar(select(Usuario).where(Usuario.rol == "admin"))


def _dia_unico():
    return date(2030, 1, 1) + timedelta(days=uuid4().int % 20000)


def _afiliar_os(session, paciente, nombre_os, descuento, vigente_desde, vigente_hasta=None):
    os_ = session.scalar(select(ObraSocial).where(ObraSocial.nombre == nombre_os))
    if os_ is None:
        os_ = ObraSocial(nombre=nombre_os, codigo="OS", activo=True)
        session.add(os_)
        session.flush()
    con = Convenio(
        obra_social_id=os_.id,
        nombre=f"Convenio {nombre_os}",
        vigente_desde=vigente_desde,
        vigente_hasta=vigente_hasta,
        descuento_global=Decimal(str(descuento)),
        activo=True,
    )
    session.add(con)
    session.flush()
    pos = PacienteObraSocial(
        paciente_id=paciente.id,
        obra_social_id=os_.id,
        convenio_id=con.id,
        nro_afiliado="A123",
        vigente_desde=vigente_desde,
        vigente_hasta=vigente_hasta,
    )
    session.add(pos)
    session.commit()
    return os_


def test_facturacion_por_medio_y_os() -> None:
    session = _session()
    try:
        usuario = _usuario(session)
        sillon, profesional = _ids(session)
        paciente = _paciente(session, "os")
        dia = _dia_unico()
        _afiliar_os(session, paciente, "OSDE", 50, dia - timedelta(days=10))
        t1 = _turno(session, paciente=paciente, profesional=profesional, sillon=sillon, dia=dia)
        t2 = _turno(
            session, paciente=paciente, profesional=profesional, sillon=sillon, dia=dia, hora=11
        )
        _movimiento(session, usuario=usuario, turno=t1, medio_pago="efectivo", monto=Decimal("1000.00"), dia=dia)
        _movimiento(
            session, usuario=usuario, turno=t2, medio_pago="transferencia", monto=Decimal("500.00"), dia=dia
        )
        res = ReportesService(session).reporte_facturacion(dia, dia)
        por_medio = {m.medio_pago: m.total for m in res.por_medio_pago}
        assert por_medio["efectivo"] == Decimal("1000.00")
        assert por_medio["transferencia"] == Decimal("500.00")
        assert res.total_ingresos == Decimal("1500.00")
        assert res.balance_neto == Decimal("1500.00")
        osde = next((o for o in res.por_obra_social if o.obra_social == "OSDE"), None)
        assert osde is not None
        assert osde.monto_os == Decimal("750.00")
        assert osde.copago_paciente == Decimal("750.00")
        assert osde.total_paciente == Decimal("1500.00")
    finally:
        session.close()


def test_facturacion_paciente_sin_afiliacion_sin_os() -> None:
    session = _session()
    try:
        usuario = _usuario(session)
        sillon, profesional = _ids(session)
        paciente = _paciente(session, "no-os")
        dia = _dia_unico()
        t = _turno(session, paciente=paciente, profesional=profesional, sillon=sillon, dia=dia)
        _movimiento(session, usuario=usuario, turno=t, medio_pago="efectivo", monto=Decimal("400.00"), dia=dia)
        res = ReportesService(session).reporte_facturacion(dia, dia)
        assert res.total_ingresos == Decimal("400.00")
        sin_os = next((o for o in res.por_obra_social if o.obra_social == "sin OS"), None)
        assert sin_os is not None
        assert sin_os.monto_os == Decimal("0.00")
        assert sin_os.copago_paciente == Decimal("400.00")
        assert sin_os.total_paciente == Decimal("400.00")
    finally:
        session.close()


def test_facturacion_rango_vacio() -> None:
    session = _session()
    try:
        dia = _dia_unico()
        res = ReportesService(session).reporte_facturacion(dia, dia)
        assert res.total_ingresos == Decimal("0.00")
        assert res.balance_neto == Decimal("0.00")
        assert res.por_medio_pago == []
        assert res.por_obra_social == []
    finally:
        session.close()
