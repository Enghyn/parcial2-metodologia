"""TDD C-21 — endpoints de facturacion (HTTP real con httpx + ASGI)."""
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


def _turno_movimiento(session, *, usuario, medio_pago, monto, dia, hora=10):
    sillon, profesional, paciente = _ids(session)
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
    fecha = datetime.combine(dia, datetime.min.time().replace(hour=hora + 1), tzinfo=TZ_CONSULTORIO)
    m = MovimientoCaja(
        tipo="ingreso",
        medio_pago=medio_pago,
        monto=monto,
        concepto="Cobro consulta",
        turno_id=t.id,
        usuario_id=usuario.id,
        fecha=fecha,
    )
    session.add(m)
    session.commit()
    return m


def _dia_unico():
    return date(2030, 1, 1) + timedelta(days=uuid4().int % 20000)


@pytest.mark.asyncio
async def test_sin_token_401() -> None:
    app, _ = _app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/facturacion")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_odontologo_403() -> None:
    app, _ = _app("odontologo")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/facturacion")
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_recepcion_200_con_ingresos() -> None:
    session = get_session_factory()()
    try:
        usuario = _usuario_db("recepcion")
        dia = _dia_unico()
        _turno_movimiento(session, usuario=usuario, medio_pago="efectivo", monto=Decimal("1200.00"), dia=dia)
        _turno_movimiento(session, usuario=usuario, medio_pago="transferencia", monto=Decimal("800.00"), dia=dia, hora=11)
    finally:
        session.close()

    app, _ = _app("recepcion")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/facturacion", params={"desde": dia.isoformat(), "hasta": dia.isoformat()})
    assert r.status_code == 200, r.text
    data = r.json()
    assert Decimal(str(data["total_ingresos"])) == Decimal("2000.00")
    assert Decimal(str(data["balance_neto"])) == Decimal("2000.00")


@pytest.mark.asyncio
async def test_desde_despues_de_hasta_422() -> None:
    app, _ = _app("recepcion")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/facturacion", params={"desde": "2030-12-01", "hasta": "2030-11-01"})
    assert r.status_code == 422, r.text
