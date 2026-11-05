"""Integración C-10: router POST /public/turnos/{token}/reprogramar (HTTP real).

Requiere base migrada + seeded.
"""
from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.rate_limit import _LIMITERS
from app.core.timezone import ahora
from app.db.session import get_session_factory
from app.main import create_app
from app.modules.agenda.models import Profesional, Sillon, Turno

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("db_disponible")]

BASE = "/api/v1/public"


def app_fresco():
    return create_app()


def _futuro(dias: int = 2):
    return ahora() + timedelta(days=dias)


def _ids() -> dict:
    session = get_session_factory()()
    try:
        sillon = session.scalar(
            select(Sillon).where(Sillon.deleted_at.is_(None)).order_by(Sillon.nombre)
        )
        prof = session.scalar(
            select(Profesional)
            .where(Profesional.deleted_at.is_(None), Profesional.activo.is_(True))
            .order_by(Profesional.matricula)
        )
        assert sillon is not None and prof is not None
        return {"sillon": sillon, "prof": prof}
    finally:
        session.close()


def _payload_reservar(ids, inicio, dni):
    return {
        "prestacion": "Consulta",
        "duracion_min": 30,
        "inicio": inicio.isoformat(),
        "profesional_id": str(ids["prof"].id),
        "sillon_id": str(ids["sillon"].id),
        "paciente": {"nombre": "Paciente Reprog", "dni": dni, "telefono": "1144556677"},
    }


def _limpiar(token: str, dni: str) -> None:
    session = get_session_factory()()
    try:
        turno = session.scalar(select(Turno).where(Turno.token_publico == token))
        if turno is not None:
            turno.soft_delete()
        session.commit()
    finally:
        session.close()


@pytest.mark.asyncio
async def test_reprogramar_turno_ok():
    _LIMITERS.clear()
    app = app_fresco()
    ids = _ids()
    dni = "R" + uuid4().hex[:12]
    inicio_original = _futuro(10)
    inicio_nuevo = _futuro(11)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(f"{BASE}/reservar", json=_payload_reservar(ids, inicio_original, dni))
        assert r.status_code == 201, r.text
        token = r.json()["token"]
        r2 = await client.post(
            f"{BASE}/turnos/{token}/reprogramar",
            json={"inicio": inicio_nuevo.isoformat()},
        )
    assert r2.status_code == 200, r2.text
    assert r2.json()["estado"] == "reservado"
    _limpiar(token, dni)


@pytest.mark.asyncio
async def test_reprogramar_token_inexistente_404():
    _LIMITERS.clear()
    app = app_fresco()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            f"{BASE}/turnos/{uuid4()}/reprogramar",
            json={"inicio": _futuro(10).isoformat()},
        )
    assert r.status_code == 404, r.text


@pytest.mark.asyncio
async def test_reprogramar_inicio_pasado_422():
    _LIMITERS.clear()
    app = app_fresco()
    ids = _ids()
    dni = "R" + uuid4().hex[:12]
    inicio_original = _futuro(10)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(f"{BASE}/reservar", json=_payload_reservar(ids, inicio_original, dni))
        assert r.status_code == 201, r.text
        token = r.json()["token"]
        pasado = ahora() - timedelta(hours=1)
        r2 = await client.post(
            f"{BASE}/turnos/{token}/reprogramar",
            json={"inicio": pasado.isoformat()},
        )
    assert r2.status_code == 422, r2.text
    _limpiar(token, dni)


@pytest.mark.asyncio
async def test_reprogramar_campos_no_permitidos_422():
    _LIMITERS.clear()
    app = app_fresco()
    ids = _ids()
    dni = "R" + uuid4().hex[:12]
    inicio_original = _futuro(10)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(f"{BASE}/reservar", json=_payload_reservar(ids, inicio_original, dni))
        assert r.status_code == 201, r.text
        token = r.json()["token"]
        r2 = await client.post(
            f"{BASE}/turnos/{token}/reprogramar",
            json={"inicio": _futuro(11).isoformat(), "sillon_id": str(ids["sillon"].id)},
        )
    assert r2.status_code == 422, r2.text
    _limpiar(token, dni)
