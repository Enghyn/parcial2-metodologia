"""Integración C-10: router QR (GET /qr/reserva.svg y /turnos/{token}/qr.svg).

Requiere base migrada + seeded.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
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
        paciente = session.scalar(select(Paciente).where(Paciente.deleted_at.is_(None)))
        assert sillon is not None and prof is not None and paciente is not None
        return {"sillon": sillon, "prof": prof, "paciente": paciente}
    finally:
        session.close()


@pytest.mark.asyncio
async def test_qr_reserva_svg_200():
    app = app_fresco()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/qr/reserva.svg")
    assert r.status_code == 200, r.text
    assert "image/svg+xml" in r.headers.get("content-type", "")
    assert len(r.content) > 0


@pytest.mark.asyncio
async def test_qr_turno_existente_200_no_store():
    app = app_fresco()
    ids = _ids()
    inicio = datetime(2027, 12, 1, 9, 0, tzinfo=UTC)
    session = get_session_factory()()
    try:
        turno = Turno(
            paciente_id=ids["paciente"].id,
            profesional_id=ids["prof"].id,
            sillon_id=ids["sillon"].id,
            prestacion="Consulta",
            inicio=inicio,
            fin=inicio + timedelta(minutes=30),
            duracion_min=30,
            estado="reservado",
            origen="publico",
        )
        session.add(turno)
        session.commit()
        token = str(turno.token_publico)
    finally:
        session.close()

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get(f"{BASE}/turnos/{token}/qr.svg")
        assert r.status_code == 200, r.text
        assert "image/svg+xml" in r.headers.get("content-type", "")
        assert r.headers.get("Cache-Control") == "no-store"
        assert len(r.content) > 0
    finally:
        session = get_session_factory()()
        try:
            t = session.scalar(select(Turno).where(Turno.token_publico == token))
            if t is not None:
                t.soft_delete()
            session.commit()
        finally:
            session.close()


@pytest.mark.asyncio
async def test_qr_turno_inexistente_404():
    app = app_fresco()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/turnos/{uuid4()}/qr.svg")
    assert r.status_code == 404, r.text
