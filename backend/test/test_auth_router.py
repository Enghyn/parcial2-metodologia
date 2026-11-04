"""TDD C-03 tarea 5.1 — endpoints de auth (HTTP real con httpx + ASGI).

`POST /api/v1/auth/login` contra la base de test Postgres (seeded, compose o
instancia local de test en 5433): 200 exitoso / 401 credenciales / 422 campo
extra (R1). `GET /api/v1/auth/me` y RBAC 403 con `get_current_user`
overrideado con un `Usuario` en memoria (sin tocar DB).

Requiere: DATABASE_URL apuntando a una base migrated + seeded
(`alembic upgrade head` + `python -m app.db.seed` desde `backend/`).
"""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.config import get_settings
from app.core.deps import get_current_user, require_role
from app.main import create_app
from app.modules.admin.models import Usuario

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("db_disponible")]

LOGIN_URL = "/api/v1/auth/login"
ME_URL = "/api/v1/auth/me"

EMAIL_SEED = "recepcion@consultorio.com"
PASSWORD_SEED = "recepcion123"


def app_fresco():
    return create_app()


def usuario_en_memoria(rol: str = "recepcion") -> Usuario:
    from uuid import uuid4

    return Usuario(
        id=uuid4(),
        nombre="Recepcionista Test",
        email=EMAIL_SEED,
        password_hash="no-importa-en-me",
        rol=rol,
        activo=True,
    )


# --- POST /login (integración, base seeded) ---


async def test_login_ok_devuelve_token_bearer() -> None:
    app = app_fresco()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(LOGIN_URL, json={"email": EMAIL_SEED, "password": PASSWORD_SEED})

    assert response.status_code == 200
    cuerpo = response.json()
    assert set(cuerpo) == {"access_token", "token_type", "expires_in"}
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["expires_in"] == get_settings().jwt_expire_min * 60
    assert "password_hash" not in cuerpo


async def test_login_ok_token_lleva_rol_correcto() -> None:
    app = app_fresco()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(LOGIN_URL, json={"email": EMAIL_SEED, "password": PASSWORD_SEED})

    from app.core.security import decodificar_token

    payload = decodificar_token(response.json()["access_token"], get_settings().jwt_secret)
    assert payload.rol == "recepcion"


async def test_login_email_normalizado_igual_al_canonico() -> None:
    app = app_fresco()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            LOGIN_URL, json={"email": "  Recepcion@Consultorio.COM ", "password": PASSWORD_SEED}
        )

    assert response.status_code == 200


async def test_login_password_mal_da_401_credenciales_invalidas() -> None:
    app = app_fresco()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(LOGIN_URL, json={"email": EMAIL_SEED, "password": "password-erroneo"})

    assert response.status_code == 401
    assert response.json() == {"error": {"code": "unauthorized", "message": "Credenciales inválidas"}}


async def test_login_email_desconocido_da_el_mismo_401() -> None:
    app = app_fresco()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            LOGIN_URL, json={"email": "fantasma@consultorio.com", "password": PASSWORD_SEED}
        )

    assert response.status_code == 401
    # No se revela cuál campo falló (anti user-enumeration)
    assert response.json() == {"error": {"code": "unauthorized", "message": "Credenciales inválidas"}}


async def test_login_campo_extra_da_422() -> None:
    """R1: schema con extra="forbid" rechaza campos no declarados."""
    app = app_fresco()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            LOGIN_URL, json={"email": EMAIL_SEED, "password": PASSWORD_SEED, "token": "inyectado"}
        )

    assert response.status_code == 422


# --- GET /me (override de get_current_user sin DB) ---


async def test_me_devuelve_perfil_sin_password_hash() -> None:
    app = app_fresco()
    app.dependency_overrides[get_current_user] = lambda: usuario_en_memoria()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(ME_URL, headers={"Authorization": "Bearer token-fake-overrideado"})

    assert response.status_code == 200
    cuerpo = response.json()
    assert set(cuerpo) == {"id", "nombre", "email", "rol"}
    assert "password_hash" not in cuerpo


async def test_me_sin_token_da_401() -> None:
    app = app_fresco()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(ME_URL)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
    assert response.json()["error"]["message"] == "No autenticado"


async def test_me_token_invalido_da_401() -> None:
    app = app_fresco()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(ME_URL, headers={"Authorization": "Bearer no-es-un-jwt"})

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Token inválido"


# --- RBAC 403 con mini-router montado solo en el test ---


async def test_endpoint_protegido_rol_odontologo_da_403() -> None:
    from fastapi import APIRouter, Depends

    app = app_fresco()
    app.dependency_overrides[get_current_user] = lambda: usuario_en_memoria(rol="odontologo")
    mini = APIRouter()

    @mini.get("/solo-admin-test", dependencies=[Depends(require_role("admin"))])
    async def endpointsolo_admin() -> dict[str, bool]:
        return {"ok": True}

    app.include_router(mini)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/solo-admin-test", headers={"Authorization": "Bearer token-fake"})

    assert response.status_code == 403
    assert response.json() == {"error": {"code": "forbidden", "message": "Rol insuficiente"}}


async def test_endpoint_protegido_rol_admitido_avanza() -> None:
    from fastapi import APIRouter, Depends

    app = app_fresco()
    app.dependency_overrides[get_current_user] = lambda: usuario_en_memoria(rol="admin")
    mini = APIRouter()

    @mini.get("/solo-admin-test", dependencies=[Depends(require_role("admin"))])
    async def endpointsolo_admin() -> dict[str, bool]:
        return {"ok": True}

    app.include_router(mini)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/solo-admin-test", headers={"Authorization": "Bearer token-fake"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}


# --- sanidad de la base de integración ---


def _pg_viva() -> bool:
    import os

    from sqlalchemy import create_engine

    try:
        engine = create_engine(
            os.environ.get("DATABASE_URL", "postgresql+psycopg://odonto:odonto@localhost:5433/odonto"),
            connect_args={"connect_timeout": 2},
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001
        return False


def test_base_de_test_tiene_usuario_de_seed() -> None:
    """Asegura que la base apuntada por DATABASE_URL está seeded (precondición)."""
    if not _pg_viva():
        import pytest as _pytest

        _pytest.skip("sin base de test Postgres viva (levantar compose o instancia localhost:5433)")
    import os

    from sqlalchemy import create_engine

    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.connect() as conn:
        filas = conn.execute(
            text("SELECT COUNT(*) FROM usuarios WHERE activo = true")
        ).scalar_one()
    assert filas >= 4, "falta seed de usuarios (python -m app.db.seed)"
