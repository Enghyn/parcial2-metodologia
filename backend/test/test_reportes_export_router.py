"""TDD C-21 — export CSV de reportes (HTTP real con httpx + ASGI)."""
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.deps import get_current_user
from app.core.timezone import TZ_CONSULTORIO
from app.db.session import get_session_factory
from app.main import create_app
from app.modules.admin.models import Usuario
from app.modules.agenda.models import Profesional, Sillon, Turno
from app.modules.caja.models import MovimientoCaja
from app.modules.clinica.models import Paciente

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("db_disponible")]

BASE = "/api/v1/reportes"


def _usuario_db(rol: str) -> Usuario:
    session = get_session_factory()()
    try:
        usuario = session.scalar(select(Usuario).where(Usuario.rol == rol, Usuario.activo.is_(True)))
        assert usuario is not None, f"falta usuario seed con rol {rol}"
        return usuario
    finally:
        session.close()


def _app(rol: str | None = None):
    app = create_app()
    usuario = _usuario_db(rol) if rol is not None else None
    if usuario is not None:
        app.dependency_overrides[get_current_user] = lambda: usuario
    return app, usuario


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


def _dia_unico():
    return date(2030, 1, 1) + timedelta(days=uuid4().int % 20000)


async def _get(client, path, params=None):
    return await client.get(f"{BASE}{path}", params=params)


def _assert_csv(r):
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers["content-disposition"]
    contenido = r.content
    assert contenido.startswith(b"\xef\xbb\xbf")  # BOM UTF-8
    texto = contenido.decode("utf-8")
    assert ";" in texto.splitlines()[0]  # separador ;
    return texto


@pytest.mark.asyncio
async def test_export_ocupacion_csv() -> None:
    session = get_session_factory()()
    try:
        sillon, profesional, paciente = _ids(session)
        dia = _dia_unico()
        _turno(session, paciente=paciente, profesional=profesional, sillon=sillon, estado="atendido", dia=dia)
    finally:
        session.close()

    app, _ = _app("recepcion")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await _get(client, "/ocupacion/export.csv", params={"desde": dia.isoformat(), "hasta": dia.isoformat()})
    texto = _assert_csv(r)
    assert "sillon" in texto or "Sillon" in texto or "recurso" in texto


@pytest.mark.asyncio
async def test_export_facturacion_csv() -> None:
    session = get_session_factory()()
    try:
        usuario = _usuario_db("recepcion")
        sillon, profesional, paciente = _ids(session)
        dia = _dia_unico()
        inicio = datetime.combine(dia, datetime.min.time().replace(hour=9), tzinfo=TZ_CONSULTORIO)
        t = Turno(
            paciente_id=paciente.id, profesional_id=profesional.id, sillon_id=sillon.id,
            prestacion="Consulta", inicio=inicio, fin=inicio + timedelta(minutes=30),
            duracion_min=30, estado="atendido",
        )
        session.add(t)
        session.flush()
        _movimiento(session, usuario=usuario, turno=t, medio_pago="efectivo", monto=Decimal("1000.00"), dia=dia)
    finally:
        session.close()

    app, _ = _app("recepcion")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await _get(client, "/facturacion/export.csv", params={"desde": dia.isoformat(), "hasta": dia.isoformat()})
    _assert_csv(r)


@pytest.mark.asyncio
async def test_export_ausentismo_csv() -> None:
    session = get_session_factory()()
    try:
        sillon, profesional, paciente = _ids(session)
        dia = _dia_unico()
        _turno(session, paciente=paciente, profesional=profesional, sillon=sillon, estado="cancelado", dia=dia)
    finally:
        session.close()

    app, _ = _app("recepcion")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await _get(client, "/ausentismo/export.csv", params={"desde": dia.isoformat(), "hasta": dia.isoformat()})
    _assert_csv(r)


@pytest.mark.asyncio
async def test_export_odontologo_facturacion_403() -> None:
    app, _ = _app("odontologo")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await _get(client, "/facturacion/export.csv")
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_export_sin_token_401() -> None:
    app, _ = _app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await _get(client, "/ocupacion/export.csv")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_export_csv_r9_no_datos_clinicos() -> None:
    session = get_session_factory()()
    try:
        sillon, profesional, paciente = _ids(session)
        dia = _dia_unico()
        _turno(session, paciente=paciente, profesional=profesional, sillon=sillon, estado="atendido", dia=dia)
    finally:
        session.close()

    app, _ = _app("recepcion")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await _get(client, "/ocupacion/export.csv", params={"desde": dia.isoformat(), "hasta": dia.isoformat()})
    texto = _assert_csv(r)
    assert "DNI" not in texto
    assert "diagnostico" not in texto.lower()
    assert paciente.dni not in texto
