"""TDD C-12 — endpoints de cierre, cuenta corriente, ajuste y export (HTTP real)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
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


def _crear_turno_y_paciente() -> tuple:
    session = get_session_factory()()
    try:
        sillon = session.scalar(
            select(Sillon).where(Sillon.deleted_at.is_(None), Sillon.activo.is_(True))
        )
        profesional = session.scalar(
            select(Profesional).where(
                Profesional.deleted_at.is_(None), Profesional.activo.is_(True)
            )
        )
        paciente = session.scalar(select(Paciente).where(Paciente.deleted_at.is_(None)))
        assert sillon is not None and profesional is not None and paciente is not None
        turno = TurnoService(session).crear(
            TurnoCreate(
                paciente_id=paciente.id,
                profesional_id=profesional.id,
                sillon_id=sillon.id,
                prestacion="Consulta",
                inicio=datetime(2030, 4, 10, 9, 0, tzinfo=TZ_CONSULTORIO),
                duracion_min=30,
            )
        )
        return turno, paciente
    finally:
        session.close()


# --- Cierres ---

@pytest.mark.asyncio
async def test_sin_token_cierres_401() -> None:
    app, _ = _app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(f"{BASE}/cierres", json={"fecha_dia": "2030-01-15"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_odontologo_cierres_403() -> None:
    app, _ = _app("odontologo")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(f"{BASE}/cierres", json={"fecha_dia": "2030-01-15"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_recepcion_cierres_403() -> None:
    app, _ = _app("recepcion")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(f"{BASE}/cierres", json={"fecha_dia": "2030-01-15"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_admin_cierra_dia_201() -> None:
    app, usuario = _app("admin")
    assert usuario is not None
    dia = _fecha_unica()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(f"{BASE}/cierres", json={"fecha_dia": dia.isoformat()})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["estado"] == "cerrado"
    assert body["fecha_dia"] == dia.isoformat()
    assert body["aprobado_por"] == str(usuario.id)
    assert body["balance"] == "0.00"


@pytest.mark.asyncio
async def test_dia_ya_cerrado_409() -> None:
    app, usuario = _app("admin")
    assert usuario is not None
    dia = _fecha_unica()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(f"{BASE}/cierres", json={"fecha_dia": dia.isoformat()})
        r = await client.post(f"{BASE}/cierres", json={"fecha_dia": dia.isoformat()})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_listar_cierres_200() -> None:
    app, _ = _app("admin")
    dia = _fecha_unica()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(f"{BASE}/cierres", json={"fecha_dia": dia.isoformat()})
        r = await client.get(f"{BASE}/cierres")
    assert r.status_code == 200
    cierres = r.json()
    assert any(c["fecha_dia"] == dia.isoformat() and c["estado"] == "cerrado" for c in cierres)


# --- Registrar movimiento bloqueado por día cerrado ---

@pytest.mark.asyncio
async def test_registrar_dia_cerrado_409() -> None:
    app, usuario = _app("recepcion")
    assert usuario is not None
    admin_app, _ = _app("admin")
    dia = _fecha_unica()
    async with AsyncClient(transport=ASGITransport(app=admin_app), base_url="http://test") as client:
        await client.post(f"{BASE}/cierres", json={"fecha_dia": dia.isoformat()})
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(f"{BASE}/movimientos", json=_payload())
    assert r.status_code == 409, r.text


# --- Cuenta corriente ---

@pytest.mark.asyncio
async def test_cuenta_corriente_200() -> None:
    app, _ = _app("recepcion")
    turno, paciente = _crear_turno_y_paciente()
    session = get_session_factory()()
    try:
        usuario = session.scalar(select(Usuario).where(Usuario.rol == "admin"))
        from app.modules.caja.models import MovimientoCaja
        session.add(
            MovimientoCaja(
                tipo="ingreso",
                medio_pago="efectivo",
                monto=Decimal("5000.00"),
                concepto="Consulta",
                usuario_id=usuario.id,
                turno_id=turno.id,
                fecha=datetime(2030, 4, 10, 10, 0, tzinfo=TZ_CONSULTORIO),
            )
        )
        session.commit()
    finally:
        session.close()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/cuenta-corriente/{paciente.id}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert Decimal(str(body["saldo"])) == Decimal("5000.00")
    assert len(body["detalle"]) == 1


@pytest.mark.asyncio
async def test_cuenta_corriente_paciente_baja_404() -> None:
    app, _ = _app("recepcion")
    session = get_session_factory()()
    try:
        paciente = session.scalar(select(Paciente).where(Paciente.deleted_at.is_(None)))
        assert paciente is not None
        paciente.soft_delete()
        session.commit()
        paciente_id = str(paciente.id)
    finally:
        session.close()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/cuenta-corriente/{paciente_id}")
    assert r.status_code == 404


# --- Ajustes ---

@pytest.mark.asyncio
async def test_ajuste_admin_201() -> None:
    app, usuario = _app("admin")
    assert usuario is not None
    turno, _paciente = _crear_turno_y_paciente()
    session = get_session_factory()()
    try:
        admin = session.scalar(select(Usuario).where(Usuario.rol == "admin"))
        from app.modules.caja.models import MovimientoCaja
        session.add(
            MovimientoCaja(
                tipo="ingreso",
                medio_pago="efectivo",
                monto=Decimal("10000.00"),
                concepto="Cobro original",
                usuario_id=admin.id,
                turno_id=turno.id,
                fecha=datetime(2030, 4, 10, 11, 0, tzinfo=TZ_CONSULTORIO),
            )
        )
        session.commit()
        movimiento_id = str(session.scalar(
            select(MovimientoCaja.id).where(MovimientoCaja.concepto == "Cobro original")
        ))
    finally:
        session.close()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            f"{BASE}/ajustes",
            json={
                "movimiento_corregido_id": movimiento_id,
                "motivo": "Corrección de cobro",
                "tipo": "egreso",
                "medio_pago": "efectivo",
                "monto": "10000.00",
                "concepto": "Anulación",
            },
        )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["motivo"] == "Corrección de cobro"
    assert body["usuario_aprobador_id"] == str(usuario.id)


@pytest.mark.asyncio
async def test_ajuste_recepcion_403() -> None:
    app, _ = _app("recepcion")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            f"{BASE}/ajustes",
            json={
                "movimiento_corregido_id": str(uuid4()),
                "motivo": "No autorizado",
                "tipo": "egreso",
                "medio_pago": "efectivo",
                "monto": "100.00",
                "concepto": "No debe crearse",
            },
        )
    assert r.status_code == 403


# --- Export CSV ---

@pytest.mark.asyncio
async def test_export_csv_200_sin_datos_clinicos() -> None:
    app, _ = _app("recepcion")
    dia = _fecha_unica()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/export", params={"fecha": dia.isoformat()})
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
    contenido = r.text
    assert "fecha,tipo,medio_pago,monto,concepto,turno_id,usuario_id" in contenido
    # No datos clínicos
    assert "diagnostico" not in contenido.lower()
    assert "odontograma" not in contenido.lower()


@pytest.mark.asyncio
async def test_export_csv_odontologo_403() -> None:
    app, _ = _app("odontologo")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/export", params={"fecha": "2030-01-01"})
    assert r.status_code == 403


# --- Sin PATCH/DELETE sobre movimientos ni cierres (append-only) ---

@pytest.mark.asyncio
async def test_no_patch_delete_movimientos() -> None:
    app, _ = _app("recepcion")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        patch = await client.patch(f"{BASE}/movimientos", json={})
        delete = await client.delete(f"{BASE}/movimientos")
    assert patch.status_code in (404, 405)
    assert delete.status_code in (404, 405)


@pytest.mark.asyncio
async def test_no_patch_delete_cierres() -> None:
    app, _ = _app("admin")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        patch = await client.patch(f"{BASE}/cierres", json={})
        delete = await client.delete(f"{BASE}/cierres")
    assert patch.status_code in (404, 405)
    assert delete.status_code in (404, 405)
