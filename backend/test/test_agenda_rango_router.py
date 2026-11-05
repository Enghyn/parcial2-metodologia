"""TDD C-09b grupo 4 — `GET /api/v1/turnos` con rango `desde`/`hasta` (HTTP real).

4.1: rango 200 y ordenado, cada variante inválida → 422 con la forma única de
error, sin token → 401, `odontologo` → 200, `fecha` intacta y query param
desconocido ignorado (compatibilidad). Semana de prueba: 2028-01-03 a 2028-01-09.
"""
import logging
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.timezone import TZ_CONSULTORIO
from app.db.session import get_session_factory
from app.main import create_app
from app.modules.admin.models import Usuario
from app.modules.agenda.models import Profesional, Sillon, Turno
from app.modules.clinica.models import Paciente

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("db_disponible")]

BASE = "/api/v1"
DESDE = "2028-01-03"
HASTA = "2028-01-09"

_LIMPIEZA_DESDE = datetime(2027, 12, 20, tzinfo=UTC)
_LIMPIEZA_HASTA = datetime(2028, 2, 20, tzinfo=UTC)


def _limpiar_datos_de_prueba() -> None:
    session = get_session_factory()()
    try:
        turnos = list(
            session.scalars(
                select(Turno).where(
                    Turno.inicio >= _LIMPIEZA_DESDE,
                    Turno.inicio < _LIMPIEZA_HASTA,
                    Turno.deleted_at.is_(None),
                )
            )
        )
        for turno in turnos:
            turno.soft_delete()
        session.commit()
    finally:
        session.close()


@pytest.fixture(autouse=True)
def _base_limpia() -> Iterator[None]:
    _limpiar_datos_de_prueba()
    yield
    _limpiar_datos_de_prueba()


@pytest.fixture
def session() -> Iterator[Session]:
    sesion = get_session_factory()()
    try:
        yield sesion
    finally:
        sesion.close()


@pytest.fixture
def ids(session: Session) -> dict[str, Any]:
    sillones = list(
        session.scalars(
            select(Sillon)
            .where(Sillon.deleted_at.is_(None), Sillon.activo.is_(True))
            .order_by(Sillon.nombre)
        )
    )
    profesionales = list(
        session.scalars(
            select(Profesional)
            .where(Profesional.deleted_at.is_(None), Profesional.activo.is_(True))
            .order_by(Profesional.matricula)
        )
    )
    pacientes = list(session.scalars(select(Paciente).where(Paciente.deleted_at.is_(None))))
    return {
        "sillon_a": sillones[0],
        "sillon_b": sillones[1],
        "prof_a": profesionales[0],
        "prof_b": profesionales[1],
        "paciente": pacientes[0],
    }


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


def _payload(ids: dict[str, Any], inicio: datetime, sillon: str = "sillon_a") -> dict[str, Any]:
    return {
        "paciente_id": str(ids["paciente"].id),
        "profesional_id": str(ids["prof_a"].id),
        "sillon_id": str(ids[sillon].id),
        "prestacion": "Consulta",
        "inicio": inicio.isoformat(),
        "duracion_min": 30,
    }


async def _crear_turno(client: AsyncClient, payload: dict[str, Any]):
    return await client.post(
        f"{BASE}/turnos", json=payload, headers={"Authorization": "Bearer t"}
    )


async def _get(client: AsyncClient, query: str):
    return await client.get(f"{BASE}/turnos?{query}", headers={"Authorization": "Bearer t"})


@pytest.mark.asyncio
async def test_rango_200_y_cuerpo_ordenado(ids: dict[str, Any]) -> None:
    app = _app()
    primera = datetime(2028, 1, 3, 9, 0, tzinfo=TZ_CONSULTORIO)
    segunda = datetime(2028, 1, 5, 15, 0, tzinfo=TZ_CONSULTORIO)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await _crear_turno(client, _payload(ids, primera))).status_code == 201
        assert (
            await _crear_turno(client, _payload(ids, segunda, sillon="sillon_b"))
        ).status_code == 201
        respuesta = await _get(client, f"desde={DESDE}&hasta={HASTA}")

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert len(cuerpo) == 2
    assert [t["inicio"] for t in cuerpo] == sorted(t["inicio"] for t in cuerpo)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        f"desde={DESDE}",
        f"hasta={HASTA}",
        f"desde={HASTA}&hasta={DESDE}",
        "desde=2028-01-03&hasta=2028-02-04",
        f"fecha=2028-01-05&desde={DESDE}&hasta={HASTA}",
        "desde=no-es-fecha&hasta=2028-01-09",
    ],
    ids=[
        "solo-desde",
        "solo-hasta",
        "rango-invertido",
        "rango-de-32-dias",
        "fecha-mas-rango",
        "fecha-malformada",
    ],
)
async def test_rango_invalido_422(query: str) -> None:
    app = _app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        respuesta = await _get(client, query)

    assert respuesta.status_code == 422, respuesta.text
    error = respuesta.json()["error"]
    assert error["code"] == "unprocessable_entity"
    assert error["message"]


@pytest.mark.asyncio
async def test_rango_sin_token_401() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        respuesta = await client.get(f"{BASE}/turnos?desde={DESDE}&hasta={HASTA}")

    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["code"] == "unauthorized"


@pytest.mark.asyncio
async def test_rango_con_rol_odontologo_200(ids: dict[str, Any]) -> None:
    app_creacion = _app("recepcion")
    inicio = datetime(2028, 1, 4, 10, 0, tzinfo=TZ_CONSULTORIO)
    async with AsyncClient(
        transport=ASGITransport(app=app_creacion), base_url="http://test"
    ) as client:
        assert (await _crear_turno(client, _payload(ids, inicio))).status_code == 201

    app = _app("odontologo")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        respuesta = await _get(client, f"desde={DESDE}&hasta={HASTA}")

    assert respuesta.status_code == 200, respuesta.text
    assert len(respuesta.json()) == 1


@pytest.mark.asyncio
async def test_fecha_sigue_devolviendo_solo_ese_dia(ids: dict[str, Any]) -> None:
    app = _app()
    martes = datetime(2028, 1, 4, 9, 0, tzinfo=TZ_CONSULTORIO)
    jueves = datetime(2028, 1, 6, 9, 0, tzinfo=TZ_CONSULTORIO)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await _crear_turno(client, _payload(ids, martes))).status_code == 201
        assert (
            await _crear_turno(client, _payload(ids, jueves, sillon="sillon_b"))
        ).status_code == 201
        respuesta = await _get(client, "fecha=2028-01-04")

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert len(cuerpo) == 1
    assert cuerpo[0]["inicio"].startswith("2028-01-04")


@pytest.mark.asyncio
async def test_query_param_desconocido_se_ignora(ids: dict[str, Any]) -> None:
    app = _app()
    inicio = datetime(2028, 1, 7, 9, 0, tzinfo=TZ_CONSULTORIO)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await _crear_turno(client, _payload(ids, inicio))).status_code == 201
        respuesta = await _get(client, f"desde={DESDE}&hasta={HASTA}&vista=semana&foo=bar")

    assert respuesta.status_code == 200, respuesta.text
    assert len(respuesta.json()) == 1


# --- 4.3 TRIANGULATE -------------------------------------------------------


@pytest.mark.asyncio
async def test_rango_mas_profesional_id(ids: dict[str, Any]) -> None:
    app = _app()
    de_prof_a = datetime(2028, 1, 4, 11, 0, tzinfo=TZ_CONSULTORIO)
    de_prof_b = datetime(2028, 1, 4, 12, 0, tzinfo=TZ_CONSULTORIO)
    payload_b = {
        **_payload(ids, de_prof_b),
        "profesional_id": str(ids["prof_b"].id),
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await _crear_turno(client, _payload(ids, de_prof_a))).status_code == 201
        assert (await _crear_turno(client, payload_b)).status_code == 201
        respuesta = await _get(
            client, f"desde={DESDE}&hasta={HASTA}&profesional_id={ids['prof_a'].id}"
        )

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert len(cuerpo) == 1
    assert cuerpo[0]["profesional_id"] == str(ids["prof_a"].id)


@pytest.mark.asyncio
async def test_rango_mas_sillon_id(ids: dict[str, Any]) -> None:
    app = _app()
    en_sillon_a = datetime(2028, 1, 5, 11, 0, tzinfo=TZ_CONSULTORIO)
    en_sillon_b = datetime(2028, 1, 5, 12, 0, tzinfo=TZ_CONSULTORIO)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await _crear_turno(client, _payload(ids, en_sillon_a))).status_code == 201
        assert (
            await _crear_turno(client, _payload(ids, en_sillon_b, sillon="sillon_b"))
        ).status_code == 201
        respuesta = await _get(
            client, f"desde={DESDE}&hasta={HASTA}&sillon_id={ids['sillon_b'].id}"
        )

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert len(cuerpo) == 1
    assert cuerpo[0]["sillon_id"] == str(ids["sillon_b"].id)


@pytest.mark.asyncio
async def test_semana_sin_turnos_devuelve_lista_vacia() -> None:
    app = _app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        respuesta = await _get(client, "desde=2028-05-01&hasta=2028-05-07")

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json() == []


@pytest.mark.asyncio
async def test_turno_out_conserva_todos_los_campos(ids: dict[str, Any]) -> None:
    app = _app()
    inicio = datetime(2028, 1, 6, 10, 0, tzinfo=TZ_CONSULTORIO)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await _crear_turno(client, _payload(ids, inicio))).status_code == 201
        respuesta = await _get(client, f"desde={DESDE}&hasta={HASTA}")

    assert respuesta.status_code == 200, respuesta.text
    turno = respuesta.json()[0]
    assert set(turno) == {
        "id",
        "paciente_id",
        "profesional_id",
        "sillon_id",
        "prestacion",
        "inicio",
        "fin",
        "duracion_min",
        "estado",
        "token_publico",
        "sena_monto",
        "notas",
        "es_sobreturno",
        "motivo_sobreturno",
        "autorizado_por",
        "created_at",
        "updated_at",
    }
    assert turno["es_sobreturno"] is False
    assert turno["motivo_sobreturno"] is None


# --- 4.5 R9 ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_rango_no_expone_datos_clinicos_en_logs_ni_en_la_url(
    ids: dict[str, Any], caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    app = _app()
    inicio = datetime(2028, 1, 7, 14, 0, tzinfo=TZ_CONSULTORIO)
    payload = _payload(ids, inicio)
    payload["prestacion"] = "Endodoncia molar 36"
    payload["notas"] = "Alergia a la penicilina"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await _crear_turno(client, payload)).status_code == 201
        caplog.clear()
        respuesta = await _get(client, f"desde={DESDE}&hasta={HASTA}")
        url = str(respuesta.request.url)

    assert respuesta.status_code == 200, respuesta.text
    assert "Endodoncia" not in url
    assert "penicilina" not in url
    assert set(respuesta.request.url.params) <= {
        "desde",
        "hasta",
        "profesional_id",
        "sillon_id",
    }
    mensajes = [
        registro.getMessage()
        for registro in caplog.records
        if registro.name.startswith("app")
    ]
    for mensaje in mensajes:
        assert "Endodoncia" not in mensaje
        assert "penicilina" not in mensaje
        assert "prestacion" not in mensaje
        assert "notas" not in mensaje
