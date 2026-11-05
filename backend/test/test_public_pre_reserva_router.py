"""Integración C-10: router POST /public/pre-reservas (HTTP real, sin auth).

Requisito: base migrada + seeded.
Usa /disponibilidad para hallar un slot libre real antes de crear la pre-reserva.
"""
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.session import get_session_factory
from app.main import create_app
from app.modules.agenda.models import Profesional, Sillon

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
        assert sillon is not None and prof is not None
        return {"sillon": sillon, "prof": prof}
    finally:
        session.close()


async def _slot_libre(client: AsyncClient, ids: dict, fecha: str) -> dict:
    """Devuelve el primer slot libre para el profesional/sillon en la fecha dada."""
    r = await client.get(
        f"{BASE}/disponibilidad",
        params={"fecha": fecha, "duracion_min": 30, "profesional_id": str(ids["prof"].id)},
    )
    assert r.status_code == 200, r.text
    slots = r.json()
    for s in slots:
        if str(s["sillon_id"]) == str(ids["sillon"].id):
            return s
    pytest.skip(f"No hay slot libre para {ids['sillon'].id} en {fecha}")


@pytest.mark.asyncio
async def test_post_pre_reserva_201_sin_auth():
    app = app_fresco()
    ids = _ids()
    fecha = "2027-03-15"  # fecha lejana, probablemente libre
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        slot = await _slot_libre(client, ids, fecha)
        payload = {
            "prestacion": "Limpieza profunda",
            "duracion_min": 30,
            "inicio": slot["inicio"],
            "profesional_id": str(ids["prof"].id),
            "sillon_id": str(ids["sillon"].id),
        }
        r = await client.post(f"{BASE}/pre-reservas", json=payload)
    assert r.status_code == 201, r.text
    cuerpo = r.json()
    assert "pre_reserva_token" in cuerpo
    assert "expira_en" in cuerpo
    # R9: sin datos sensibles del paciente en la respuesta
    assert "dni" not in cuerpo
    assert "telefono" not in cuerpo
    assert "nombre" not in cuerpo


@pytest.mark.asyncio
async def test_post_pre_reserva_hueco_ocupado_409():
    app = app_fresco()
    ids = _ids()
    fecha = "2027-03-16"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        slot = await _slot_libre(client, ids, fecha)
        payload = {
            "prestacion": "Limpieza profunda",
            "duracion_min": 30,
            "inicio": slot["inicio"],
            "profesional_id": str(ids["prof"].id),
            "sillon_id": str(ids["sillon"].id),
        }
        r1 = await client.post(f"{BASE}/pre-reservas", json=payload)
        assert r1.status_code == 201, r1.text
        # La misma pre-reserva duplicada -> 409
        r2 = await client.post(f"{BASE}/pre-reservas", json=payload)
    assert r2.status_code == 409, r2.text


@pytest.mark.asyncio
async def test_post_pre_reserva_campo_extra_422():
    app = app_fresco()
    ids = _ids()
    fecha = "2027-03-17"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        slot = await _slot_libre(client, ids, fecha)
        payload = {
            "prestacion": "Limpieza profunda",
            "duracion_min": 30,
            "inicio": slot["inicio"],
            "profesional_id": str(ids["prof"].id),
            "sillon_id": str(ids["sillon"].id),
            "campo_inexistente": "no deberia aceptar",
        }
        r = await client.post(f"{BASE}/pre-reservas", json=payload)
    assert r.status_code == 422, r.text


@pytest.mark.asyncio
async def test_post_pre_reserva_inicio_pasado_422():
    app = app_fresco()
    ids = _ids()
    pasado = datetime(2020, 1, 1, 9, 0, tzinfo=UTC)
    payload = {
        "prestacion": "Limpieza profunda",
        "duracion_min": 30,
        "inicio": pasado.isoformat(),
        "profesional_id": str(ids["prof"].id),
        "sillon_id": str(ids["sillon"].id),
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(f"{BASE}/pre-reservas", json=payload)
    assert r.status_code == 422, r.text
