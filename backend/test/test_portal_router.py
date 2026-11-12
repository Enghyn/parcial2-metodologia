"""TDD C-18 tareas 3.1-3.3 — endpoints públicos del portal (HTTP real, sin auth).

Requiere base migrada + seeded (alembic upgrade head + python -m app.db.seed).
"""
from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import registry  # noqa: F401  (registra todas las tablas para las FK)
from app.db.session import get_session_factory
from app.main import create_app
from app.modules.clinica.models import Paciente
from app.modules.pagos.models import IntentoPago, Pago
from app.modules.presupuestos.models import ItemPresupuesto, Presupuesto

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("db_disponible")]

BASE = "/api/v1/public"

_CLAVES_PROHIBIDAS = {"id", "paciente_id", "presupuesto_id", "movimiento_id", "token_publico"}
_CLAVES_SENSIBLES = {"dni", "telefono", "email", "paciente", "ficha"}


@pytest.fixture(autouse=True)
def _sin_rate_limit(monkeypatch) -> None:
    """Desactiva el rate-limit público para no acoplar el test al contador."""
    from app.core import rate_limit

    monkeypatch.setattr(
        rate_limit,
        "get_settings",
        lambda: get_settings().model_copy(update={"rate_limit_enabled": False}),
    )


def _session() -> Session:
    return get_session_factory()()


def _crear_presupuesto(session: Session, *, estado: str = "enviado") -> Presupuesto:
    paciente = session.scalar(select(Paciente).where(Paciente.deleted_at.is_(None)))
    assert paciente is not None
    p = Presupuesto(paciente_id=paciente.id, estado=estado, total=0.0)
    session.add(p)
    session.flush()
    session.add(
        ItemPresupuesto(
            presupuesto_id=p.id,
            descripcion="Consulta",
            cantidad=2,
            arancel=1000.0,
            copago=100.0,
        )
    )
    p.total = 1900.0
    session.commit()
    session.refresh(p)
    return p


def _limpiar(presupuesto_id: UUID) -> None:
    session = _session()
    try:
        session.rollback()
        pago_ids = list(
            session.scalars(select(Pago.id).where(Pago.presupuesto_id == presupuesto_id))
        )
        if pago_ids:
            session.query(IntentoPago).filter(IntentoPago.pago_id.in_(pago_ids)).delete(
                synchronize_session=False
            )
            session.query(Pago).filter(Pago.presupuesto_id == presupuesto_id).delete(
                synchronize_session=False
            )
        session.query(ItemPresupuesto).filter(
            ItemPresupuesto.presupuesto_id == presupuesto_id
        ).delete(synchronize_session=False)
        session.query(Presupuesto).filter(Presupuesto.id == presupuesto_id).delete(
            synchronize_session=False
        )
        session.commit()
    finally:
        session.close()


def _cliente() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test")


def _assert_sin_ids_ni_pii(cuerpo: dict) -> None:
    assert _CLAVES_PROHIBIDAS.isdisjoint(cuerpo.keys())
    assert _CLAVES_SENSIBLES.isdisjoint(cuerpo.keys())


# --- Tarea 3.1/3.2: presupuesto público ---


@pytest.mark.asyncio
async def test_get_presupuesto_200_sin_ids_internos() -> None:
    session = _session()
    p = _crear_presupuesto(session)
    session.close()
    try:
        async with _cliente() as client:
            r = await client.get(f"{BASE}/presupuestos/{p.token_publico}")
        assert r.status_code == 200, r.text
        cuerpo = r.json()
        assert set(cuerpo.keys()) == {"estado", "total", "items"}
        _assert_sin_ids_ni_pii(cuerpo)
        assert cuerpo["estado"] == "enviado"
        assert float(cuerpo["total"]) == 1900.0
        assert set(cuerpo["items"][0].keys()) == {"descripcion", "cantidad", "arancel", "copago"}
    finally:
        _limpiar(p.id)


@pytest.mark.asyncio
async def test_get_presupuesto_token_inexistente_404_generico() -> None:
    async with _cliente() as client:
        r = await client.get(f"{BASE}/presupuestos/{uuid4()}")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


@pytest.mark.asyncio
async def test_aprobar_presupuesto_200() -> None:
    session = _session()
    p = _crear_presupuesto(session, estado="enviado")
    session.close()
    try:
        async with _cliente() as client:
            r = await client.post(
                f"{BASE}/presupuestos/{p.token_publico}/aprobar",
                json={"firma": "María López"},
            )
        assert r.status_code == 200, r.text
        assert r.json()["estado"] == "aprobado"
        _assert_sin_ids_ni_pii(r.json())
    finally:
        _limpiar(p.id)


@pytest.mark.asyncio
async def test_aprobar_token_inexistente_404() -> None:
    async with _cliente() as client:
        r = await client.post(
            f"{BASE}/presupuestos/{uuid4()}/aprobar", json={"firma": "María López"}
        )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_aprobar_presupuesto_cobrado_409() -> None:
    session = _session()
    p = _crear_presupuesto(session, estado="cobrado")
    session.close()
    try:
        async with _cliente() as client:
            r = await client.post(
                f"{BASE}/presupuestos/{p.token_publico}/aprobar",
                json={"firma": "María López"},
            )
        assert r.status_code == 409
    finally:
        _limpiar(p.id)


@pytest.mark.asyncio
async def test_rechazar_presupuesto_200() -> None:
    session = _session()
    p = _crear_presupuesto(session, estado="enviado")
    session.close()
    try:
        async with _cliente() as client:
            r = await client.post(
                f"{BASE}/presupuestos/{p.token_publico}/rechazar", json={"motivo": "Muy caro"}
            )
        assert r.status_code == 200, r.text
        assert r.json()["estado"] == "rechazado"
    finally:
        _limpiar(p.id)


# --- Tarea 3.3: campo no declarado → 422 (R1) ---


@pytest.mark.asyncio
async def test_aprobar_campo_extra_422() -> None:
    session = _session()
    p = _crear_presupuesto(session, estado="enviado")
    session.close()
    try:
        async with _cliente() as client:
            r = await client.post(
                f"{BASE}/presupuestos/{p.token_publico}/aprobar",
                json={"firma": "María López", "foo": "bar"},
            )
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "unprocessable_entity"
    finally:
        _limpiar(p.id)


@pytest.mark.asyncio
async def test_rechazar_campo_extra_422() -> None:
    session = _session()
    p = _crear_presupuesto(session, estado="enviado")
    session.close()
    try:
        async with _cliente() as client:
            r = await client.post(
                f"{BASE}/presupuestos/{p.token_publico}/rechazar",
                json={"motivo": "Muy caro", "foo": "bar"},
            )
        assert r.status_code == 422
    finally:
        _limpiar(p.id)


# --- Tarea 3.1/3.2: pago público ---


@pytest.mark.asyncio
async def test_get_pago_pendiente_200() -> None:
    session = _session()
    p = _crear_presupuesto(session, estado="aprobado")
    session.close()
    try:
        async with _cliente() as client:
            r = await client.get(f"{BASE}/pagos/{p.token_publico}")
        assert r.status_code == 200, r.text
        cuerpo = r.json()
        assert set(cuerpo.keys()) == {"estado", "monto", "confirmado_en"}
        _assert_sin_ids_ni_pii(cuerpo)
        assert cuerpo["estado"] == "pendiente"
        assert float(cuerpo["monto"]) == 1900.0
        assert cuerpo["confirmado_en"] is None
    finally:
        _limpiar(p.id)


@pytest.mark.asyncio
async def test_confirmar_pago_200_sin_ids_internos() -> None:
    session = _session()
    p = _crear_presupuesto(session, estado="aprobado")
    session.close()
    try:
        async with _cliente() as client:
            r = await client.post(f"{BASE}/pagos/{p.token_publico}/confirmar")
        assert r.status_code == 200, r.text
        cuerpo = r.json()
        assert set(cuerpo.keys()) == {"estado", "monto", "confirmado_en"}
        _assert_sin_ids_ni_pii(cuerpo)
        assert cuerpo["estado"] == "aprobado"
        assert float(cuerpo["monto"]) == 1900.0
    finally:
        _limpiar(p.id)


@pytest.mark.asyncio
async def test_confirmar_pago_no_aprobado_409() -> None:
    session = _session()
    p = _crear_presupuesto(session, estado="enviado")
    session.close()
    try:
        async with _cliente() as client:
            r = await client.post(f"{BASE}/pagos/{p.token_publico}/confirmar")
        assert r.status_code == 409
    finally:
        _limpiar(p.id)


@pytest.mark.asyncio
async def test_confirmar_pago_token_inexistente_404() -> None:
    async with _cliente() as client:
        r = await client.post(f"{BASE}/pagos/{uuid4()}/confirmar")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


@pytest.mark.asyncio
async def test_get_pago_token_inexistente_404() -> None:
    async with _cliente() as client:
        r = await client.get(f"{BASE}/pagos/{uuid4()}")
    assert r.status_code == 404
