"""Tests de integración del visor y export de auditoría (C-20)."""
from __future__ import annotations

import csv
import io
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.deps import get_current_user
from app.db.session import get_session_factory
from app.main import create_app
from app.modules.admin.models import Usuario
from app.modules.audit.models import Auditoria
from app.modules.audit.service import registrar_auditoria


BASE = "/api/v1/auditoria"
CAJA_BASE = "/api/v1/caja"

pytestmark = pytest.mark.integration


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


@pytest.mark.asyncio
async def test_admin_lista_auditoria_200() -> None:
    app, _ = _app("admin")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(BASE)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_no_admin_recibe_403_en_listar() -> None:
    for rol in ("recepcion", "odontologo"):
        app, _ = _app(rol)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get(BASE)
        assert r.status_code == 403, (rol, r.status_code, r.text)


@pytest.mark.asyncio
async def test_export_csv_200_con_cabecera() -> None:
    app, _ = _app("admin")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/export")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers.get("content-disposition", "")
    reader = csv.reader(io.StringIO(r.text))
    cabecera = next(reader)
    assert cabecera == ["id", "fecha", "usuario_id", "accion", "recurso", "recurso_id", "diff", "ip", "user_agent"]


@pytest.mark.asyncio
async def test_export_sin_permiso_403() -> None:
    app, _ = _app("recepcion")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/export")
    assert r.status_code == 403, r.text


@pytest.mark.asyncio
async def test_crear_movimiento_genera_auditoria() -> None:
    admin = _usuario_db("admin")
    app, _ = _app("admin")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            f"{CAJA_BASE}/movimientos",
            json={
                "tipo": "ingreso",
                "medio_pago": "efectivo",
                "monto": "1000.00",
                "concepto": "Cobro de consulta",
            },
        )
    assert r.status_code == 201, r.text
    movimiento_id = r.json()["id"]

    session = get_session_factory()()
    try:
        filas = session.scalars(
            select(Auditoria).where(Auditoria.recurso == "movimiento_caja")
        ).all()
        assert filas, "no se generó auditoría al crear el movimiento"
        ultima = max(filas, key=lambda a: a.fecha)
        assert ultima.accion == "crear"
        assert str(ultima.recurso_id) == movimiento_id
        assert ultima.usuario_id == admin.id
    finally:
        session.close()


@pytest.mark.asyncio
async def test_filtro_por_recurso() -> None:
    app, _ = _app("admin")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(BASE, params={"recurso": "movimiento_caja"})
    assert r.status_code == 200, r.text
    for item in r.json():
        assert item["recurso"] == "movimiento_caja"


@pytest.mark.asyncio
async def test_paginacion_size() -> None:
    app, _ = _app("admin")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(BASE, params={"page": 1, "size": 1})
    assert r.status_code == 200, r.text
    assert len(r.json()) <= 1


@pytest.mark.asyncio
async def test_masking_en_db() -> None:
    admin = _usuario_db("admin")
    session = get_session_factory()()
    try:
        registrar_auditoria(
            session,
            usuario_id=admin.id,
            accion="crear",
            recurso="hallazgo_pieza",
            recurso_id=uuid4(),
            diff={"motivo": "dolor molar", "observacion": "caries profunda", "monto": "100"},
        )
        session.commit()
        fila = session.scalars(
            select(Auditoria).where(Auditoria.recurso == "hallazgo_pieza")
        ).all()[-1]
        assert fila.diff["motivo"] == "[REDACTED]"
        assert fila.diff["observacion"] == "[REDACTED]"
        assert fila.diff["monto"] == "100"
    finally:
        session.close()


@pytest.mark.asyncio
async def test_export_no_filtra_datos_sensibles() -> None:
    admin = _usuario_db("admin")
    session = get_session_factory()()
    try:
        registrar_auditoria(
            session,
            usuario_id=admin.id,
            accion="crear",
            recurso="hallazgo_pieza",
            recurso_id=uuid4(),
            diff={"motivo": "dolor molar", "observacion": "caries profunda", "monto": "100"},
        )
        session.commit()
    finally:
        session.close()

    app, _ = _app("admin")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/export", params={"recurso": "hallazgo_pieza"})
    assert r.status_code == 200, r.text
    assert "[REDACTED]" in r.text
    assert "dolor molar" not in r.text
    assert "caries profunda" not in r.text