"""TDD C-03 tarea 4.1 — dependencias RBAC (`app.core.deps`).

`get_current_user` (revalidación por request: activo=False o inexistente →
401) y `require_role(*roles)` (factory; rol no admitido → 403 "Rol
insuficiente", D7). Probadas contra la función con tokens generados en el
test (sin app, sin DB real: fake de sesión para la revalidación).
"""
from uuid import uuid4

import bcrypt
import jwt as pyjwt
import pytest
from fastapi import HTTPException

from app.core.deps import get_current_user, require_role
from app.modules.admin.models import Usuario

SECRETO = "secreto-de-test-de-mas-de-32-caracteres-config"


class FakeSesionUsuarios:
    """Sesión falsa: solo `scalar`, la única operación que deps usa."""

    def __init__(self, usuario: Usuario | None) -> None:
        self.usuario = usuario
        self.consultas: list[object] = []

    def scalar(self, statement: object) -> Usuario | None:
        self.consultas.append(statement)
        return self.usuario


def usuario_en_memoria(rol: str = "recepcion", activo: bool = True) -> Usuario:
    return Usuario(
        id=uuid4(),
        nombre="Recepcionista",
        email="recepcion@consultorio.com",
        password_hash=bcrypt.hashpw(b"recepcion123", bcrypt.gensalt(rounds=4)).decode("utf-8"),
        rol=rol,
        activo=activo,
    )


# --- require_role: RBAC en el backend (R8) ---


def test_require_role_admite_el_rol_y_devuelve_usuario() -> None:
    dependencia = require_role("admin", "recepcion")
    usuario = usuario_en_memoria(rol="recepcion")

    assert dependencia(usuario) is usuario


def test_require_role_rechaza_con_403() -> None:
    dependencia = require_role("admin", "recepcion")
    usuario = usuario_en_memoria(rol="odontologo")

    with pytest.raises(HTTPException) as exc_info:
        dependencia(usuario)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Rol insuficiente"


def test_require_role_varios_roles_permitidos() -> None:
    dependencia = require_role("admin", "recepcion", "odontologo")
    usuario = usuario_en_memoria(rol="odontologo")

    assert dependencia(usuario) is usuario


# --- get_current_user: token + revalidación de baja por request ---


async def test_token_vigente_resuelve_usuario_activo() -> None:
    usuario = usuario_en_memoria()
    from app.core.security import crear_access_token

    token = crear_access_token(sub=str(usuario.id), rol="recepcion", secret=SECRETO, expire_min=60)
    sesion = FakeSesionUsuarios(usuario)

    resuelto = await get_current_user(token, sesion)  # type: ignore[arg-type]

    assert resuelto is usuario
    assert len(sesion.consultas) == 1


async def test_token_expirado_da_401_token_expirado() -> None:
    from app.core.security import crear_access_token

    token = crear_access_token(sub=str(uuid4()), rol="recepcion", secret=SECRETO, expire_min=-1)
    sesion = FakeSesionUsuarios(None)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token, sesion)  # type: ignore[arg-type]
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token expirado"


async def test_token_con_firma_ajena_da_401_token_invalido() -> None:
    token = pyjwt.encode(
        {"sub": str(uuid4()), "rol": "recepcion", "iat": 1699000000, "exp": 1799999999},
        "clave-de-otro-servicio-totalmente-distinta",
        algorithm="HS256",
    )
    sesion = FakeSesionUsuarios(None)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token, sesion)  # type: ignore[arg-type]
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token inválido"


async def test_token_malformado_da_401_token_invalido() -> None:
    sesion = FakeSesionUsuarios(None)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user("no-es-un-jwt", sesion)  # type: ignore[arg-type]
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token inválido"


async def test_usuario_no_existe_da_401() -> None:
    """Revalidación por request: sub que ya no existe en la base → 401."""
    from app.core.security import crear_access_token

    token = crear_access_token(sub=str(uuid4()), rol="admin", secret=SECRETO, expire_min=60)
    sesion = FakeSesionUsuarios(None)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token, sesion)  # type: ignore[arg-type]
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "No autenticado"


async def test_usuario_dado_de_baja_con_token_vigente_da_401() -> None:
    """Spec auth: la baja lógica corta sesiones al instante (RN-SEG-02)."""
    from app.core.security import crear_access_token

    usuario = usuario_en_memoria(activo=False)
    token = crear_access_token(sub=str(usuario.id), rol="recepcion", secret=SECRETO, expire_min=60)
    sesion = FakeSesionUsuarios(usuario)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token, sesion)  # type: ignore[arg-type]
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "No autenticado"

