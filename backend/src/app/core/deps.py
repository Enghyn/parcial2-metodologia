"""Dependencias FastAPI de autenticación y autorización (C-03, D6).

Contrato que consume C-04+ vía `Depends`:
- `get_current_user(token, db)` → `Usuario` (revalida `activo` por request).
- `require_role(*roles)` → factory de dependencia de RBAC (R8: SIEMPRE en el
  backend; el frontend solo oculta la UI).

Mensajes fijos D7 (es-AR, única forma de error en core/errors):
- 401 `No autenticado` / `Token expirado` / `Token inválido`
- 403 `Rol insuficiente`

R9: acá nunca se loguean tokens ni credenciales.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decodificar_token
from app.db.session import get_db
from app.modules.admin.models import Usuario


class _BearerOAuth2(OAuth2PasswordBearer):
    """OAuth2PasswordBearer con mensaje D7: header ausente o malformado →
    401 `No autenticado` (el default "Not authenticated" es inglés y no es
    parte del contrato de errores)."""

    async def __call__(self, request: Request) -> str:
        try:
            return await super().__call__(request)
        except HTTPException as exc:
            if exc.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No autenticado",
                    headers={"WWW-Authenticate": "Bearer"},
                ) from None
            raise


oauth2_scheme = _BearerOAuth2(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> Usuario:
    """Resuelve el `Usuario` del token vigente y revalida la baja lógica (D6).

    El token no vale por sí solo: si el usuario ya no existe o está
    `activo=False` (dado de baja), responde 401 aunque el JWT siga vigente.
    """
    try:
        payload = decodificar_token(token, get_settings().jwt_secret)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado") from None
    except (jwt.PyJWTError, ValidationError, ValueError):
        raise HTTPException(status_code=401, detail="Token inválido") from None

    usuario = db.scalar(select(Usuario).where(Usuario.id == UUID(payload.sub)))
    if usuario is None or not usuario.activo:
        # Revalidación por request (D6): la baja lógica corta sesiones al instante.
        raise HTTPException(status_code=401, detail="No autenticado")
    return usuario


def require_role(*roles: str) -> Callable[..., Usuario]:
    """Factory de dependencia: `Depends(require_role("admin", "recepcion"))`.

    Resuelve primero el usuario vía `get_current_user`; si su rol no está
    entre los admitidos responde 403 "Rol insuficiente" (D7) sin ejecutar la
    lógica del endpoint. Devuelve el Usuario por si el endpoint lo usa.
    """

    def dependencia(
        usuario: Annotated[Usuario, Depends(get_current_user)],
    ) -> Usuario:
        if usuario.rol not in roles:
            raise HTTPException(status_code=403, detail="Rol insuficiente")
        return usuario

    return dependencia
