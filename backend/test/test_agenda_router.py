"""TDD C-04 grupo 5 — endpoints de agenda (HTTP real con httpx + ASGI)."""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.deps import get_current_user
from app.core.timezone import TZ_CONSULTORIO
from app.db.session import get_session_factory
from app.main import create_app
from app.modules.admin.models import Usuario
from app.modules.agenda.models import Bloqueo, Profesional, Sillon, Turno
from app.modules.clinica.models import Paciente

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("db_disponible")]

BASE = "/api/v1"

# Rango de fechas que usan los tests de este módulo. El fixture limpiador
# borra solo lo que vive acá para no tocar datos de demo ni de otros tests.
_RANGO_DESDE = datetime(2027, 1, 9, tzinfo=UTC)
_RANGO_HASTA = datetime(2027, 1, 21, tzinfo=UTC)


def _limpiar_datos_de_prueba() -> None:
    """Restaura la base: turnos con borrado lógico (R13) y bloqueos eliminados."""
    session = get_session_factory()()
    try:
        turnos = list(
            session.scalars(
                select(Turno).where(
                    Turno.inicio >= _RANGO_DESDE,
                    Turno.inicio < _RANGO_HASTA,
                    Turno.deleted_at.is_(None),
                )
            )
        )
        for turno in turnos:
            turno.soft_delete()
        bloqueos = list(
            session.scalars(
                select(Bloqueo).where(
                    Bloqueo.desde >= _RANGO_DESDE, Bloqueo.desde < _RANGO_HASTA
                )
            )
        )
        for bloqueo in bloqueos:
            session.delete(bloqueo)
        session.commit()
    finally:
        session.close()


@pytest.fixture(autouse=True)
def _base_limpia() -> None:
    """Hace la suite repetible: limpia antes y después de cada test."""
    _limpiar_datos_de_prueba()
    yield
    _limpiar_datos_de_prueba()


def app_fresco():
    return create_app()


def usuario_en_memoria(rol: str = "recepcion") -> Usuario:
    return Usuario(
        id=uuid4(),
        nombre="Tester",
        email="tester@consultorio.com",
        password_hash="x",
        rol=rol,
        activo=True,
    )


def _seed_ids() -> dict:
    session = get_session_factory()()
    try:
        sillones = list(session.scalars(select(Sillon).where(Sillon.deleted_at.is_(None)).order_by(Sillon.nombre)))
        profesionales = list(session.scalars(select(Profesional).where(Profesional.deleted_at.is_(None)).order_by(Profesional.matricula)))
        pacientes = list(session.scalars(select(Paciente).where(Paciente.deleted_at.is_(None))))
        return {
            "sillon_a": sillones[0],
            "sillon_b": sillones[1],
            "prof_a": profesionales[0],
            "prof_b": profesionales[1],
            "paciente": pacientes[0],
        }
    finally:
        session.close()


IDS: dict = {}


@pytest.fixture(scope="module", autouse=True)
def _cargar_ids(db_disponible) -> None:
    IDS.update(_seed_ids())


def _turno_payload(sillon, prof, paciente, inicio, duracion=30) -> dict:
    return {
        "paciente_id": str(paciente.id),
        "profesional_id": str(prof.id),
        "sillon_id": str(sillon.id),
        "prestacion": "Consulta",
        "inicio": inicio.isoformat(),
        "duracion_min": duracion,
    }


async def _post_turno(client, payload, headers=None):
    return await client.post(f"{BASE}/turnos", json=payload, headers=headers or {})


@pytest.mark.asyncio
async def test_crear_hueco_libre_201() -> None:
    app = app_fresco()
    app.dependency_overrides[get_current_user] = lambda: usuario_en_memoria("recepcion")
    ids = IDS
    inicio = datetime(2027, 1, 10, 9, 0, tzinfo=UTC)
    payload = _turno_payload(ids["sillon_a"], ids["prof_a"], ids["paciente"], inicio)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await _post_turno(client, payload, {"Authorization": "Bearer t"})
    assert r.status_code == 201, r.text
    cuerpo = r.json()
    assert "id" in cuerpo
    assert cuerpo["estado"] == "reservado"


@pytest.mark.asyncio
async def test_conflicto_mismo_sillon_409() -> None:
    app = app_fresco()
    app.dependency_overrides[get_current_user] = lambda: usuario_en_memoria("recepcion")
    ids = IDS
    inicio = datetime(2027, 1, 11, 9, 0, tzinfo=UTC)
    payload = _turno_payload(ids["sillon_a"], ids["prof_a"], ids["paciente"], inicio)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r1 = await _post_turno(client, payload, {"Authorization": "Bearer t"})
        assert r1.status_code == 201
        # mismo sillón, profesional distinto
        payload2 = _turno_payload(ids["sillon_a"], ids["prof_b"], ids["paciente"], inicio)
        r2 = await _post_turno(client, payload2, {"Authorization": "Bearer t"})
    assert r2.status_code == 409
    assert r2.json()["error"]["code"] == "conflict"
    assert "sillón" in r2.json()["error"]["message"]


@pytest.mark.asyncio
async def test_conflicto_mismo_profesional_distinto_sillon_409() -> None:
    app = app_fresco()
    app.dependency_overrides[get_current_user] = lambda: usuario_en_memoria("recepcion")
    ids = IDS
    inicio = datetime(2027, 1, 12, 9, 0, tzinfo=UTC)
    payload = _turno_payload(ids["sillon_a"], ids["prof_a"], ids["paciente"], inicio)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r1 = await _post_turno(client, payload, {"Authorization": "Bearer t"})
        assert r1.status_code == 201
        payload2 = _turno_payload(ids["sillon_b"], ids["prof_a"], ids["paciente"], inicio)
        r2 = await _post_turno(client, payload2, {"Authorization": "Bearer t"})
    assert r2.status_code == 409
    assert "profesional" in r2.json()["error"]["message"]


@pytest.mark.asyncio
async def test_mismo_horario_distinto_recurso_ok() -> None:
    app = app_fresco()
    app.dependency_overrides[get_current_user] = lambda: usuario_en_memoria("recepcion")
    ids = IDS
    inicio = datetime(2027, 1, 13, 9, 0, tzinfo=UTC)
    payload1 = _turno_payload(ids["sillon_a"], ids["prof_a"], ids["paciente"], inicio)
    payload2 = _turno_payload(ids["sillon_b"], ids["prof_b"], ids["paciente"], inicio)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r1 = await _post_turno(client, payload1, {"Authorization": "Bearer t"})
        r2 = await _post_turno(client, payload2, {"Authorization": "Bearer t"})
    assert r1.status_code == 201
    assert r2.status_code == 201


@pytest.mark.asyncio
async def test_creacion_sobre_turno_cancelado_ok() -> None:
    app = app_fresco()
    app.dependency_overrides[get_current_user] = lambda: usuario_en_memoria("recepcion")
    ids = IDS
    inicio = datetime(2027, 1, 14, 9, 0, tzinfo=UTC)
    payload = _turno_payload(ids["sillon_a"], ids["prof_a"], ids["paciente"], inicio)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r1 = await _post_turno(client, payload, {"Authorization": "Bearer t"})
        assert r1.status_code == 201
        tid = r1.json()["id"]
        # cancelar
        rpatch = await client.patch(f"{BASE}/turnos/{tid}/estado", json={"estado": "cancelado"}, headers={"Authorization": "Bearer t"})
        assert rpatch.status_code == 200
        # recrear mismo rango
        r2 = await _post_turno(client, payload, {"Authorization": "Bearer t"})
    assert r2.status_code == 201


@pytest.mark.asyncio
async def test_sin_token_401() -> None:
    app = app_fresco()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/turnos")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_rol_insuficiente_403() -> None:
    app = app_fresco()
    app.dependency_overrides[get_current_user] = lambda: usuario_en_memoria("odontologo")
    ids = IDS
    inicio = datetime(2027, 1, 15, 9, 0, tzinfo=UTC)
    payload = _turno_payload(ids["sillon_a"], ids["prof_a"], ids["paciente"], inicio)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await _post_turno(client, payload, {"Authorization": "Bearer t"})
    assert r.status_code == 403
    assert r.json() == {"error": {"code": "forbidden", "message": "Rol insuficiente"}}


@pytest.mark.asyncio
async def test_campo_extra_422() -> None:
    app = app_fresco()
    app.dependency_overrides[get_current_user] = lambda: usuario_en_memoria("recepcion")
    ids = IDS
    inicio = datetime(2027, 1, 16, 9, 0, tzinfo=UTC)
    payload = _turno_payload(ids["sillon_a"], ids["prof_a"], ids["paciente"], inicio)
    payload["foo"] = "bar"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await _post_turno(client, payload, {"Authorization": "Bearer t"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_patch_estado_inexistente_404() -> None:
    app = app_fresco()
    app.dependency_overrides[get_current_user] = lambda: usuario_en_memoria("recepcion")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.patch(f"{BASE}/turnos/{uuid4()}/estado", json={"estado": "confirmado"}, headers={"Authorization": "Bearer t"})
    assert r.status_code == 404
    assert r.json()["error"]["message"] == "Turno no encontrado"


@pytest.mark.asyncio
async def test_bloqueo_post_delete() -> None:
    app = app_fresco()
    app.dependency_overrides[get_current_user] = lambda: usuario_en_memoria("recepcion")
    ids = IDS
    inicio = datetime(2027, 1, 17, 9, 0, tzinfo=UTC)
    fin = inicio + timedelta(minutes=60)
    payload = {
        "sillon_id": str(ids["sillon_a"].id),
        "desde": inicio.isoformat(),
        "hasta": fin.isoformat(),
        "motivo": "Limpieza",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r1 = await client.post(f"{BASE}/bloqueos", json=payload, headers={"Authorization": "Bearer t"})
        assert r1.status_code == 201 or r1.status_code == 200, r1.text
        bid = r1.json()["id"]
        r2 = await client.delete(f"{BASE}/bloqueos/{bid}", headers={"Authorization": "Bearer t"})
        assert r2.status_code in (200, 204), r2.text
        # eliminar de nuevo → 404
        r3 = await client.delete(f"{BASE}/bloqueos/{bid}", headers={"Authorization": "Bearer t"})
        assert r3.status_code == 404


@pytest.mark.asyncio
async def test_delete_bloqueo_inexistente_404() -> None:
    app = app_fresco()
    app.dependency_overrides[get_current_user] = lambda: usuario_en_memoria("recepcion")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.delete(f"{BASE}/bloqueos/{uuid4()}", headers={"Authorization": "Bearer t"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_turnos_ok() -> None:
    app = app_fresco()
    app.dependency_overrides[get_current_user] = lambda: usuario_en_memoria("odontologo")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get(f"{BASE}/turnos", headers={"Authorization": "Bearer t"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_patch_estado_exitoso() -> None:
    app = app_fresco()
    app.dependency_overrides[get_current_user] = lambda: usuario_en_memoria("recepcion")
    ids = IDS
    inicio = datetime(2027, 1, 18, 9, 0, tzinfo=UTC)
    payload = _turno_payload(ids["sillon_a"], ids["prof_a"], ids["paciente"], inicio)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r1 = await _post_turno(client, payload, {"Authorization": "Bearer t"})
        assert r1.status_code == 201
        tid = r1.json()["id"]
        r2 = await client.patch(f"{BASE}/turnos/{tid}/estado", json={"estado": "confirmado"}, headers={"Authorization": "Bearer t"})
    assert r2.status_code == 200
    assert r2.json()["estado"] == "confirmado"


@pytest.mark.asyncio
async def test_bloqueo_turno_conflicto_409() -> None:
    app = app_fresco()
    app.dependency_overrides[get_current_user] = lambda: usuario_en_memoria("recepcion")
    ids = IDS
    inicio = datetime(2027, 1, 19, 9, 0, tzinfo=UTC)
    fin = inicio + timedelta(minutes=30)
    bloqueo_payload = {
        "sillon_id": str(ids["sillon_a"].id),
        "desde": inicio.isoformat(),
        "hasta": fin.isoformat(),
        "motivo": "Bloqueo",
    }
    turno_payload = _turno_payload(ids["sillon_a"], ids["prof_a"], ids["paciente"], inicio)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        rb = await client.post(f"{BASE}/bloqueos", json=bloqueo_payload, headers={"Authorization": "Bearer t"})
        assert rb.status_code in (200, 201)
        rt = await _post_turno(client, turno_payload, {"Authorization": "Bearer t"})
    assert rt.status_code == 409
    assert "bloqueado" in rt.json()["error"]["message"]


@pytest.mark.asyncio
async def test_turno_inicio_pasado_422() -> None:
    app = app_fresco()
    app.dependency_overrides[get_current_user] = lambda: usuario_en_memoria("recepcion")
    ids = IDS
    inicio = datetime(2020, 1, 1, 9, 0, tzinfo=TZ_CONSULTORIO)
    payload = _turno_payload(ids["sillon_a"], ids["prof_a"], ids["paciente"], inicio)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await _post_turno(client, payload, {"Authorization": "Bearer t"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_turno_recurso_inexistente_404() -> None:
    app = app_fresco()
    app.dependency_overrides[get_current_user] = lambda: usuario_en_memoria("recepcion")
    ids = IDS
    payload = {
        "paciente_id": str(ids["paciente"].id),
        "profesional_id": str(ids["prof_a"].id),
        "sillon_id": str(uuid4()),
        "prestacion": "Consulta",
        "inicio": datetime(2027, 1, 20, 9, 0, tzinfo=TZ_CONSULTORIO).isoformat(),
        "duracion_min": 30,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await _post_turno(client, payload, {"Authorization": "Bearer t"})
    assert r.status_code == 404