"""TDD C-21 — prueba de integración punta a punta de reportes."""
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
from app.modules.agenda.models import Profesional, Sillon, Turno
from app.modules.caja.models import MovimientoCaja
from app.modules.clinica.models import Paciente

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("db_disponible")]

BASE = "/api/v1/reportes"


def _usuario_db(rol: str) -> Usuario:
    session = get_session_factory()()
    try:
        return session.scalar(select(Usuario).where(Usuario.rol == rol, Usuario.activo.is_(True)))
    finally:
        session.close()


def _app(rol: str | None = None):
    app = create_app()
    usuario = _usuario_db(rol) if rol is not None else None
    if usuario is not None:
        app.dependency_overrides[get_current_user] = lambda: usuario
    return app, usuario


def _ids(session):
    sillon = session.scalar(select(Sillon).where(Sillon.deleted_at.is_(None), Sillon.activo.is_(True)))
    profesional = session.scalar(select(Profesional).where(Profesional.deleted_at.is_(None), Profesional.activo.is_(True)))
    paciente = session.scalar(select(Paciente).where(Paciente.deleted_at.is_(None)))
    return sillon, profesional, paciente


def _escenario(session, usuario, dia):
    sillon, profesional, paciente = _ids(session)
    # turnos: 2 atendidos, 1 cancelado, 1 ausente (mismo paciente -> 1 recuperado)
    for i, estado in enumerate(["atendido", "atendido", "cancelado", "ausente"]):
        inicio = datetime.combine(dia, datetime.min.time().replace(hour=9 + i), tzinfo=TZ_CONSULTORIO)
        t = Turno(
            paciente_id=paciente.id,
            profesional_id=profesional.id,
            sillon_id=sillon.id,
            prestacion="Consulta",
            inicio=inicio,
            fin=inicio + timedelta(minutes=30),
            duracion_min=30,
            estado=estado,
        )
        session.add(t)
        session.flush()
        # movimiento solo para los atendidos (cobro real)
        if estado == "atendido":
            m = MovimientoCaja(
                tipo="ingreso",
                medio_pago="efectivo" if i == 0 else "transferencia",
                monto=Decimal("5000.00") if i == 0 else Decimal("3000.00"),
                concepto="Cobro consulta",
                turno_id=t.id,
                usuario_id=usuario.id,
                fecha=inicio + timedelta(minutes=30),
            )
            session.add(m)
    session.commit()
    return paciente


def _dia_unico():
    return date(2030, 1, 1) + timedelta(days=uuid4().int % 20000)


@pytest.mark.asyncio
async def test_integracion_reportes_rbac_y_csv() -> None:
    session = get_session_factory()()
    try:
        usuario = _usuario_db("recepcion")
        dia = _dia_unico()
        _escenario(session, usuario, dia)
    finally:
        session.close()

    async def cliente(rol: str | None):
        app, _ = _app(rol)
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    params = {"desde": dia.isoformat(), "hasta": dia.isoformat()}

    # --- sin token: 401 en los tres reportes ---
    async with await cliente(None) as client:
        for path in ("/ocupacion", "/facturacion", "/ausentismo"):
            r = await client.get(f"{BASE}{path}", params=params)
            assert r.status_code == 401, (path, r.text)

    # --- odontologo: 403 en facturacion y ausentismo, 200 en ocupacion propia ---
    async with await cliente("odontologo") as client:
        r = await client.get(f"{BASE}/facturacion", params=params)
        assert r.status_code == 403
        r = await client.get(f"{BASE}/ausentismo", params=params)
        assert r.status_code == 403
        r = await client.get(f"{BASE}/ocupacion", params=params)
        assert r.status_code == 200, r.text

    # --- recepcion: 200 en los tres ---
    async with await cliente("recepcion") as client:
        ro = await client.get(f"{BASE}/ocupacion", params=params)
        rf = await client.get(f"{BASE}/facturacion", params=params)
        ra = await client.get(f"{BASE}/ausentismo", params=params)
        assert ro.status_code == 200 and rf.status_code == 200 and ra.status_code == 200

        do = ro.json()
        df = rf.json()
        da = ra.json()
        assert any(f.get("atendido", 0) >= 1 for f in do.get("sillones", []))
        assert Decimal(str(df["total_ingresos"])) == Decimal("8000.00")  # 5000 + 3000
        assert da["cancelados"] == 1 and da["no_presentados"] == 1
        assert da["tasa_ausentismo"] == round(2 / 4, 4)

        # --- export CSV de los tres reportes ---
        for path in ("/ocupacion/export.csv", "/facturacion/export.csv", "/ausentismo/export.csv"):
            r = await client.get(f"{BASE}{path}", params=params)
            assert r.status_code == 200, path
            assert r.headers["content-type"].startswith("text/csv")
            assert "attachment" in r.headers["content-disposition"]
            contenido = r.content.decode("utf-8")
            assert contenido.startswith("\ufeff")  # BOM
            assert ";" in contenido.splitlines()[0]  # separador ;
            assert "DNI" not in contenido  # R9

    # --- odontologo tampoco lee export de facturacion ---
    async with await cliente("odontologo") as client:
        r = await client.get(f"{BASE}/facturacion/export.csv", params=params)
        assert r.status_code == 403
