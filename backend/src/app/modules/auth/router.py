"""Router auth (C-03): `POST /login` público + `GET /me` con Bearer (D4/D7).

Montado desde `app.api.v1.router` con `include_router(auth.router)` →
`/api/v1/auth/*`. El 401/403 con la forma única de error lo renderiza
`core/errors`. Sin logs de credenciales ni tokens (R9).
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.core.security import crear_access_token
from app.db.session import get_db
from app.modules.admin.models import Usuario
from app.modules.auth.schemas import LoginIn, TokenOut, UsuarioOut
from app.modules.auth.service import SessionUsuarioFinder, autenticar_usuario

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(datos: LoginIn, db: Annotated[Session, Depends(get_db)]) -> TokenOut:
    """Login del personal interno (público). 401 genérico anti user-enumeration:
    el mensaje no revela si falló el email o el password (D7)."""
    usuario = autenticar_usuario(SessionUsuarioFinder(db), datos.email, datos.password)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    settings = get_settings()
    return TokenOut(
        access_token=crear_access_token(
            sub=str(usuario.id),
            rol=usuario.rol,
            secret=settings.jwt_secret,
            expire_min=settings.jwt_expire_min,
        ),
        token_type="bearer",
        expires_in=settings.jwt_expire_min * 60,
    )


@router.get("/me", response_model=UsuarioOut)
def me(usuario_actual: Annotated[Usuario, Depends(get_current_user)]) -> UsuarioOut:
    """Perfil mínimo del usuario autenticado (nunca `password_hash`, R9)."""
    return UsuarioOut.model_validate(usuario_actual)
