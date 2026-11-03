"""Primitivas de seguridad: hash bcrypt + JWT HS256 (C-03 auth-jwt-roles).

Funciones PURAS, sin FastAPI ni DB (D4): el HTTP lo monta `core.deps.py`.
Claims mínimos del access token (D5 / R9): `sub`, `rol`, `iat`, `exp` —
nunca email, nombre ni `tenant_id` (R2, mono-consultorio, DD-02).
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Final

import bcrypt
import jwt
from pydantic import BaseModel, ConfigDict, model_validator

from app.modules.admin.models import ROLES_USUARIO

_BCRYPT_ROUNDS: Final[int] = 12  # mismo coste que el seed C-02: los usuarios del seed loguean igual
_ALGORITMO: Final[str] = "HS256"


def hash_password(password: str) -> str:
    """Hash bcrypt con 12 rounds; formato compatible con `verify_password`."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(raw: str, hashed: str) -> bool:
    """Verificación constant-time con bcrypt; un hash corrupto devuelve False."""
    try:
        return bcrypt.checkpw(raw.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def crear_access_token(sub: str, rol: str, secret: str, expire_min: int) -> str:
    """Access token HS256 con claims mínimos y expiración configurable (D5)."""
    if rol not in ROLES_USUARIO:
        raise ValueError(f"rol desconocido para emitir un token: {rol}")
    now = datetime.now(tz=UTC)
    now_ts = int(now.timestamp())
    claims: dict[str, object] = {
        "sub": sub,
        "rol": rol,
        "iat": now_ts,
        "exp": now_ts + expire_min * 60,
    }
    return jwt.encode(claims, secret, algorithm=_ALGORITMO)


class TokenPayload(BaseModel):
    """Claims decodificados del access token (D5). `extra="forbid"`: un claim
    inesperado o un rol fuera del catálogo rechaza el token (no pasa por defecto)."""

    model_config = ConfigDict(extra="forbid")

    sub: str
    rol: str
    iat: int
    exp: int

    @model_validator(mode="after")
    def _validar_rol_contra_catalogo(self) -> TokenPayload:
        """Única fuente de roles: `ROLES_USUARIO` de modules/admin (C-02)."""
        if self.rol not in ROLES_USUARIO:
            raise ValueError(f"rol fuera del catálogo ROLES_USUARIO: {self.rol}")
        return self


def decodificar_token(token: str, secret: str) -> TokenPayload:
    """Verifica firma HS256 + expiración y valida los claims.

    `jwt.ExpiredSignatureError` (exp vencido) y `jwt.InvalidSignatureError` /
    `jwt.DecodeError` (firma o token inválidos) se propagan: deps.py los mapea
    a 401 con mensaje fijo (D7).
    """
    claims: dict[str, object] = jwt.decode(
        token,
        secret,
        algorithms=[_ALGORITMO],
        options={"require": ["sub", "rol", "exp"]},
    )
    return TokenPayload.model_validate(claims)
