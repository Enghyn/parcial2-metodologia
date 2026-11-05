"""Catálogos internos de agenda (defecto detectado en C-09b).

Sin `GET /sillones` ni `GET /profesionales`, `cargarCatalogos()` de la SPA cae al
fallback con IDs ficticios y ninguna grilla (diaria ni semanal) puede asociar un
turno real a su sillón. Estos tests fijan el contrato mínimo de lectura.
"""
import logging
from collections.abc import Iterator
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.deps import get_current_user
from app.db import registry  # noqa: F401
from app.db.session import get_session_factory
from app.main import create_app
from app.modules.admin.models import Usuario
from app.modules.agenda.models import Profesional, Sillon

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("db_disponible")]

BASE = "/api/v1"


def _usuario(rol: str = "recepcion") -> Usuario:
    return Usuario(
        id=uuid4(),
        nombre="Tester",
        email="tester@consultorio.com",
        password_hash="x",
        rol=rol,
        activo=True,
    )


def _app(rol: str = "recepcion"):
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: _usuario(rol)
    return app


@pytest.fixture
def session() -> Iterator:
    sesion = get_session_factory()()
    try:
        yield sesion
    finally:
        sesion.close()


async def _get(rol: str, path: str, headers: dict[str, str] | None = None):
    app = _app(rol)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.get(f"{path}", headers=headers if headers is not None else {"Authorization": "Bearer t"})


@pytest.mark.asyncio
async def test_sillones_devuelve_los_activos_ordenados() -> None:
    respuesta = await _get("recepcion", f"{BASE}/sillones")

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert len(cuerpo) >= 2
    assert set(cuerpo[0]) == {"id", "nombre", "activo"}
    assert all(sillon["activo"] is True for sillon in cuerpo)
    nombres = [sillon["nombre"] for sillon in cuerpo]
    assert nombres == sorted(nombres)
    assert "Sillón 1" in nombres


@pytest.mark.asyncio
async def test_sillones_excluye_borrados_e_inactivos(session) -> None:
    borrado = Sillon(nombre=f"Temp {uuid4().hex[:8]}", activo=True)
    inactivo = Sillon(nombre=f"Temp Inactivo {uuid4().hex[:8]}", activo=False)
    session.add_all([borrado, inactivo])
    session.commit()
    borrado.soft_delete()
    session.commit()

    respuesta = await _get("recepcion", f"{BASE}/sillones")

    ids = {sillon["id"] for sillon in respuesta.json()}
    assert str(borrado.id) not in ids
    assert str(inactivo.id) not in ids

    # Sin residuos para las próximas corridas (activaría una fila extra en la grilla).
    inactivo.soft_delete()
    session.commit()


@pytest.mark.asyncio
async def test_profesionales_devuelve_los_activos_ordenados() -> None:
    respuesta = await _get("odontologo", f"{BASE}/profesionales")

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert set(cuerpo[0]) == {"id", "nombre"}
    nombres = [profesional["nombre"] for profesional in cuerpo]
    assert nombres == sorted(nombres)
    assert "Dr. Pérez" in nombres
    assert "Dra. Gómez" in nombres
    assert all("Inactivo" not in nombre for nombre in nombres)


@pytest.mark.asyncio
async def test_profesionales_excluye_inactivos(session) -> None:
    inactivo = Profesional(
        nombre=f"Temp {uuid4().hex[:8]}",
        matricula=f"MP-{uuid4().hex[:6]}",
        especialidad="Test",
        duracion_default_min=30,
        activo=False,
    )
    session.add(inactivo)
    session.commit()

    respuesta = await _get("admin", f"{BASE}/profesionales")

    assert str(inactivo.id) not in {profesional["id"] for profesional in respuesta.json()}

    inactivo.soft_delete()
    session.commit()


@pytest.mark.asyncio
async def test_catalogos_sin_token_401() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sillones = await client.get(f"{BASE}/sillones")
        profesionales = await client.get(f"{BASE}/profesionales")

    assert sillones.status_code == 401
    assert profesionales.status_code == 401


@pytest.mark.asyncio
async def test_catalogos_no_loguean_datos_de_pacientes(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)

    respuesta = await _get("recepcion", f"{BASE}/sillones")

    assert respuesta.status_code == 200
    mensajes = [registro.getMessage() for registro in caplog.records if registro.name.startswith("app")]
    assert all("paciente" not in mensaje.lower() for mensaje in mensajes)


def test_los_sillones_del_seed_son_los_que_consume_la_grilla(session) -> None:
    """La grilla necesita al menos tres sillones activos para 7 × 3 (US-001)."""
    activos = list(
        session.scalars(
            select(Sillon).where(Sillon.deleted_at.is_(None), Sillon.activo.is_(True))
        )
    )
    assert len(activos) >= 3
