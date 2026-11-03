"""Servicio de autenticación (C-03): lógica pura de login sin HTTP (D4/D8).

`autenticar_usuario` depende del Protocol mínimo `UsuarioFinder`
(`find_by_email(email)`) para poder testearse con un fake (D8). El router
usa el adaptador `SessionUsuarioFinder` sobre la sesión de SQLAlchemy.

R9: aquí no se loguea ninguna credencial (ni password, ni email crudo).
"""
from __future__ import annotations

from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.modules.admin.models import Usuario


def normalizar_email(email: str) -> str:
    """Trim + minúsculas: misma forma canónica que el `validates` del modelo."""
    return email.strip().lower()


class UsuarioFinder(Protocol):
    """Contrato mínimo de resolución de usuario por email (D8)."""

    def find_by_email(self, email: str) -> Usuario | None: ...


class SessionUsuarioFinder:
    """Adaptador real sobre una sesión SQLAlchemy (lo consume el router)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def find_by_email(self, email: str) -> Usuario | None:
        return self.db.scalar(
            select(Usuario).where(func.lower(Usuario.email) == normalizar_email(email))
        )


def autenticar_usuario(db: UsuarioFinder, email: str, password: str) -> Usuario | None:
    """Login del personal interno (D8).

    Devuelve el `Usuario` si credenciales + actividad son válidos, o `None`
    (password mal, email desconocido o `activo=False`). El 401 genérico lo
    monta el router: este service no revela cuál campo falló.
    """
    email_normalizado = normalizar_email(email)
    usuario = db.find_by_email(email_normalizado)
    if usuario is None or not usuario.activo:
        return None
    if not verify_password(password, usuario.password_hash):
        return None
    return usuario
