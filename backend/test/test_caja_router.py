"""TDD C-08 — endpoints de caja (HTTP real con httpx + ASGI)."""
from datetime import date, datetime, time, timedelta
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
from app.modules.agenda.models import Profesional, Sillon
from app.modules.agenda.schemas import TurnoCreate
from app.modules.agenda.service import TurnoService
from app.modules.caja.models import MovimientoCaja
from app.modules.clinica.models import Paciente

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("db_disponible")]

BASE = "/api/v1/caja"


def _usuario_db(rol: str) -> Usuario:
    session = get_session_factory()()
    try:
        usuario = session.scalar(
            select(Usuario).where(Usuario.rol == rol, Usuario.activo.is_(True))
        )
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


def _payload(**extra: object) -> dict:
    data = {
        "tipo": "ingreso",
        "medio_pago": "efectivo",
        "monto": "10000.00",
        "concepto": "Cobro de consulta",
    }
    data.update(extra)
    return data


def _fecha_unica() -> date:
    return date(2030, 1, 1) + timedelta(days=uuid4().int % 20000)


def _crear_turno_borrado() -> str:
    session = get_session_factory()()
    try:
        sillon = session.scalar(select(Sillon).where(Sillon.deleted_at.is_(None)))
        profesional = session.scalar(select(Profesional).where(Profesional.deleted_at.is_(None)))
        paciente = session.scalar(select(Paciente).where(Paciente.deleted_at.is_(None)))
        assert sillon is not None and profesional is not None and paciente is not None
        turno = TurnoService(session).crear(
            TurnoCreate(
                paciente_id=paciente.id,
                profesional_id=profesional.id,
                sillon_id=sillon.id,
                prestacion="Consulta",
                inicio=datetime(2027, 4, 10, 9, 0, tzinfo=TZ_CONSULTORIO),
                duracion_min=30,
            )
        )
        turno.soft_delete()
        session.commit()
        return str(turno.id)
    finally:
        session.close()


@pytest.mark.asyncio
async def test_sin_token_401() -> None:
    app, _ = _app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/movimientos")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_odontologo_403() -> None:
    app, _ = _app("odontologo")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/movimientos")
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_crear_ingreso_201() -> None:
    app, usuario = _app("recepcion")
    assert usuario is not None
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(f"{BASE}/movimientos", json=_payload())
    assert r.status_code == 201, r.text
    assert r.json()["usuario_id"] == str(usuario.id)


@pytest.mark.asyncio
async def test_body_con_usuario_422() -> None:
    app, _ = _app("recepcion")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(f"{BASE}/movimientos", json=_payload(usuario_id=str(uuid4())))
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_monto_cero_422() -> None:
    app, _ = _app("recepcion")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(f"{BASE}/movimientos", json=_payload(monto="0"))
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_turno_borrado_404() -> None:
    app, _ = _app("recepcion")
    turno_id = _crear_turno_borrado()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(f"{BASE}/movimientos", json=_payload(turno_id=turno_id))
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_listado_y_resumen_diario() -> None:
    app, usuario = _app("recepcion")
    assert usuario is not None
    dia = _fecha_unica()
    session = get_session_factory()()
    try:
        session.add(
            MovimientoCaja(
                tipo="ingreso",
                medio_pago="efectivo",
                monto=Decimal("100.00"),
                concepto="Test resumen",
                usuario_id=usuario.id,
                fecha=datetime.combine(dia, time(10, 0), tzinfo=TZ_CONSULTORIO),
            )
        )
        session.commit()
    finally:
        session.close()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        rl = await client.get(f"{BASE}/movimientos", params={"fecha": dia.isoformat()})
        rr = await client.get(f"{BASE}/resumen-diario", params={"fecha": dia.isoformat()})
    assert rl.status_code == 200
    assert any(m["concepto"] == "Test resumen" for m in rl.json())
    assert rr.status_code == 200
    assert Decimal(str(rr.json()["total_ingresos"])) == Decimal("100.00")


@pytest.mark.asyncio
async def test_resumen_vacio() -> None:
    app, _ = _app("recepcion")
    dia = _fecha_unica()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/resumen-diario", params={"fecha": dia.isoformat()})
    assert r.status_code == 200
    assert Decimal(str(r.json()["total_ingresos"])) == Decimal("0.00")
    assert Decimal(str(r.json()["balance"])) == Decimal("0.00")


@pytest.mark.asyncio
async def test_no_hay_patch_ni_delete() -> None:
    app, _ = _app("recepcion")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        patch = await client.patch(f"{BASE}/movimientos", json={})
        delete = await client.delete(f"{BASE}/movimientos")
    assert patch.status_code in (404, 405)
    assert delete.status_code in (404, 405)
