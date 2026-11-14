"""TDD C-21 — endpoints de ocupacion (HTTP real con httpx + ASGI)."""
from datetime import date, datetime, timedelta
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


def _dia_unico():
    return date(2030, 1, 1) + timedelta(days=uuid4().int % 20000)


@pytest.mark.asyncio
async def test_sin_token_401() -> None:
    app, _ = _app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/ocupacion")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_odontologo_facturacion_403() -> None:
    app, _ = _app("odontologo")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/facturacion")
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_odontologo_ausentismo_403() -> None:
    app, _ = _app("odontologo")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/ausentismo")
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_odontologo_ocupacion_otro_profesional_403() -> None:
    # Profesional vinculado al usuario odontologo del seed
    session = get_session_factory()()
    try:
        odontologo = session.scalar(select(Usuario).where(Usuario.rol == "odontologo", Usuario.activo.is_(True)))
        assert odontologo is not None
        propio = session.scalar(
            select(Profesional).where(Profesional.usuario_id == odontologo.id)
        )
        assert propio is not None
        otro = session.scalar(
            select(Profesional).where(
                Profesional.id != propio.id,
                Profesional.deleted_at.is_(None),
                Profesional.activo.is_(True),
            )
        )
        assert otro is not None
        sillon = session.scalar(
            select(Sillon).where(Sillon.deleted_at.is_(None), Sillon.activo.is_(True))
        )
        paciente = session.scalar(select(Paciente).where(Paciente.deleted_at.is_(None)))
        assert sillon is not None and paciente is not None
        _turno(session, paciente=paciente, profesional=propio, sillon=sillon, estado="atendido", dia=_dia_unico())
    finally:
        session.close()

    app, _ = _app("odontologo")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/ocupacion", params={"profesional_id": str(otro.id)})
    assert r.status_code == 403, r.text


@pytest.mark.asyncio
async def test_recepcion_ocupacion_200() -> None:
    session = get_session_factory()()
    try:
        sillon, profesional, paciente = _ids(session)
        dia = _dia_unico()
        _turno(session, paciente=paciente, profesional=profesional, sillon=sillon, estado="atendido", dia=dia)
        _turno(session, paciente=paciente, profesional=profesional, sillon=sillon, estado="cancelado", dia=dia, hora=10)
    finally:
        session.close()

    app, _ = _app("recepcion")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/ocupacion", params={"desde": dia.isoformat(), "hasta": dia.isoformat()})
    assert r.status_code == 200, r.text
    data = r.json()
    assert any(f.get("atendido", 0) >= 1 for f in data.get("sillones", []))


@pytest.mark.asyncio
async def test_desde_despues_de_hasta_422() -> None:
    app, _ = _app("recepcion")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(
            f"{BASE}/ocupacion",
            params={"desde": "2030-12-01", "hasta": "2030-11-01"},
        )
    assert r.status_code == 422, r.text
