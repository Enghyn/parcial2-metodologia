"""TDD C-07 — endpoints de ficha clínica (HTTP real con httpx + ASGI)."""
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.deps import get_current_user
from app.db.session import get_session_factory
from app.main import create_app
from app.modules.admin.models import Usuario
from app.modules.clinica.models import Paciente

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("db_disponible")]

BASE = "/api/v1"


def _usuario(rol: str) -> Usuario:
    return Usuario(
        id=uuid4(),
        nombre=f"Test {rol}",
        email=f"{rol}@test.com",
        password_hash="x",
        rol=rol,
        activo=True,
    )


def _app(rol: str | None = None):
    app = create_app()
    if rol is not None:

        def _override() -> Usuario:
            return _usuario(rol)

        app.dependency_overrides[get_current_user] = _override
    return app


def _dni() -> str:
    return "R" + uuid4().hex[:12]


def _payload(dni: str) -> dict:
    return {"nombre": "Paciente Router", "dni": dni, "telefono": "1144556677"}


def _limpiar(dni: str) -> None:
    session = get_session_factory()()
    try:
        paciente = session.scalar(select(Paciente).where(Paciente.dni == dni))
        if paciente is not None:
            paciente.soft_delete()
            session.commit()
    finally:
        session.close()


@pytest.mark.asyncio
async def test_sin_token_401() -> None:
    app = _app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/pacientes")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_recepcion_no_puede_editar_pieza_403() -> None:
    dni = _dni()
    app = _app("recepcion")
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(f"{BASE}/pacientes", json=_payload(dni))
            assert r.status_code == 201, r.text
            pid = r.json()["id"]
            rp = await client.put(
                f"{BASE}/pacientes/{pid}/odontograma/piezas/11",
                json={"estado": "caries"},
            )
        assert rp.status_code == 403
    finally:
        _limpiar(dni)


@pytest.mark.asyncio
async def test_flujo_paciente_y_odontograma() -> None:
    dni = _dni()
    app = _app("admin")
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(f"{BASE}/pacientes", json=_payload(dni))
            assert r.status_code == 201, r.text
            pid = r.json()["id"]
            listado = await client.get(f"{BASE}/pacientes", params={"q": dni})
            assert any(p["id"] == pid for p in listado.json())
            od = await client.get(f"{BASE}/pacientes/{pid}/odontograma")
            assert od.status_code == 200
            assert od.json()["hallazgos"] == []

            app.dependency_overrides[get_current_user] = lambda: _usuario("odontologo")
            h = await client.put(
                f"{BASE}/pacientes/{pid}/odontograma/piezas/16",
                json={"estado": "caries", "observacion": "Revisar"},
            )
            assert h.status_code == 200, h.text
            assert h.json()["pieza"] == 16
            od2 = await client.get(f"{BASE}/pacientes/{pid}/odontograma")
            assert len(od2.json()["hallazgos"]) == 1
    finally:
        _limpiar(dni)


@pytest.mark.asyncio
async def test_pieza_invalida_422() -> None:
    dni = _dni()
    app = _app("admin")
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(f"{BASE}/pacientes", json=_payload(dni))
            pid = r.json()["id"]
            app.dependency_overrides[get_current_user] = lambda: _usuario("odontologo")
            rp = await client.put(
                f"{BASE}/pacientes/{pid}/odontograma/piezas/19",
                json={"estado": "caries"},
            )
        assert rp.status_code == 422
    finally:
        _limpiar(dni)


@pytest.mark.asyncio
async def test_paciente_borrado_404() -> None:
    dni = _dni()
    app = _app("admin")
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(f"{BASE}/pacientes", json=_payload(dni))
            pid = r.json()["id"]
        session = get_session_factory()()
        try:
            paciente = session.scalar(select(Paciente).where(Paciente.dni == dni))
            assert paciente is not None
            paciente.soft_delete()
            session.commit()
        finally:
            session.close()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r2 = await client.get(f"{BASE}/pacientes/{pid}/odontograma")
        assert r2.status_code == 404
    finally:
        _limpiar(dni)
