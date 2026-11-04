"""TDD C-06 grupos 3-5 — endpoints públicos (HTTP real con httpx + ASGI, sin auth)."""
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.session import get_session_factory
from app.main import create_app
from app.modules.agenda.models import Profesional, Sillon, Turno
from app.modules.clinica.models import Paciente

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("db_disponible")]

BASE = "/api/v1/public"


def app_fresco():
    return create_app()


def _seed_ids() -> dict:
    session = get_session_factory()()
    try:
        sillones = list(
            session.scalars(
                select(Sillon).where(Sillon.deleted_at.is_(None)).order_by(Sillon.nombre)
            )
        )
        profesionales = list(
            session.scalars(
                select(Profesional)
                .where(Profesional.deleted_at.is_(None), Profesional.activo.is_(True))
                .order_by(Profesional.matricula)
            )
        )
        return {"sillon": sillones[0], "prof": profesionales[0]}
    finally:
        session.close()


def _dni_unico() -> str:
    return "R" + uuid4().hex[:12]


def _payload(ids: dict, inicio: datetime, dni: str) -> dict:
    return {
        "prestacion": "Consulta",
        "duracion_min": 30,
        "inicio": inicio.isoformat(),
        "profesional_id": str(ids["prof"].id),
        "sillon_id": str(ids["sillon"].id),
        "paciente": {"nombre": "Paciente Router", "dni": dni, "telefono": "1144556677"},
    }


def _limpiar(token: str, dni: str) -> None:
    session = get_session_factory()()
    try:
        turno = session.scalar(select(Turno).where(Turno.token_publico == token))
        if turno is not None:
            turno.soft_delete()
        paciente = session.scalar(select(Paciente).where(Paciente.dni == dni))
        if paciente is not None:
            paciente.soft_delete()
        session.commit()
    finally:
        session.close()


@pytest.mark.asyncio
async def test_disponibilidad_publica_sin_auth_200() -> None:
    app = app_fresco()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/disponibilidad", params={"fecha": "2027-10-01", "duracion_min": 30})
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)
    assert r.json() != []


@pytest.mark.asyncio
async def test_disponibilidad_sin_fecha_422() -> None:
    app = app_fresco()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/disponibilidad", params={"duracion_min": 30})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "unprocessable_entity"


@pytest.mark.asyncio
async def test_profesionales_publicos_200() -> None:
    app = app_fresco()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/profesionales")
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert isinstance(cuerpo, list)
    assert cuerpo != []
    assert set(cuerpo[0].keys()) == {"id", "nombre"}


@pytest.mark.asyncio
async def test_reservar_201_sin_datos_sensibles() -> None:
    app = app_fresco()
    ids = _seed_ids()
    dni = _dni_unico()
    inicio = datetime(2027, 10, 2, 9, 0, tzinfo=UTC)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(f"{BASE}/reservar", json=_payload(ids, inicio, dni))
    assert r.status_code == 201, r.text
    cuerpo = r.json()
    assert cuerpo["estado"] == "reservado"
    assert cuerpo["token"] is not None
    assert "dni" not in cuerpo
    assert "telefono" not in cuerpo
    _limpiar(cuerpo["token"], dni)


@pytest.mark.asyncio
async def test_reservar_campo_extra_422() -> None:
    app = app_fresco()
    ids = _seed_ids()
    dni = _dni_unico()
    payload = _payload(ids, datetime(2027, 10, 3, 9, 0, tzinfo=UTC), dni)
    payload["foo"] = "bar"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(f"{BASE}/reservar", json=payload)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_reservar_faltan_campos_422() -> None:
    app = app_fresco()
    ids = _seed_ids()
    payload = _payload(ids, datetime(2027, 10, 4, 9, 0, tzinfo=UTC), _dni_unico())
    payload["paciente"].pop("telefono")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(f"{BASE}/reservar", json=payload)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_get_turno_por_token_200_y_404() -> None:
    app = app_fresco()
    ids = _seed_ids()
    dni = _dni_unico()
    inicio = datetime(2027, 10, 5, 9, 0, tzinfo=UTC)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(f"{BASE}/reservar", json=_payload(ids, inicio, dni))
        assert r.status_code == 201, r.text
        token = r.json()["token"]
        r_ok = await client.get(f"{BASE}/turnos/{token}")
        assert r_ok.status_code == 200
        assert r_ok.json()["token"] == token
        r_404 = await client.get(f"{BASE}/turnos/{uuid4()}")
        assert r_404.status_code == 404
        assert r_404.json()["error"]["message"] == "Turno no encontrado"
    _limpiar(token, dni)


@pytest.mark.asyncio
async def test_cancelar_por_token_200_y_409() -> None:
    app = app_fresco()
    ids = _seed_ids()
    dni = _dni_unico()
    inicio = datetime(2027, 10, 6, 9, 0, tzinfo=UTC)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(f"{BASE}/reservar", json=_payload(ids, inicio, dni))
        assert r.status_code == 201, r.text
        token = r.json()["token"]
        r1 = await client.post(f"{BASE}/turnos/{token}/cancelar")
        assert r1.status_code == 200
        assert r1.json()["estado"] == "cancelado"
        r2 = await client.post(f"{BASE}/turnos/{token}/cancelar")
        assert r2.status_code == 409
        r3 = await client.post(f"{BASE}/turnos/{uuid4()}/cancelar")
        assert r3.status_code == 404
    _limpiar(token, dni)
