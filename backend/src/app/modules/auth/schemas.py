"""Schemas HTTP del módulo auth (C-03, D7). JSON snake_case (R5).

R1: TODOS los schemas de API declaran `extra="forbid"` — un campo no
declarado (p. ej. `token` inyectado en el login) rechaza con 422.
"""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LoginIn(BaseModel):
    """Cuerpo del login. Campos mínimos; `extra="forbid"` (R1)."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=5, max_length=150)
    password: str = Field(min_length=1, max_length=128)


class TokenOut(BaseModel):
    """Access token emitido (D7): `expires_in` en segundos, para el contador
    de sesión del front (C-05). `extra="forbid"` también aquí (R1)."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: Literal["bearer"]
    expires_in: int


class UsuarioOut(BaseModel):
    """Perfil del usuario autenticado (D7): jamás expone `password_hash` (R9)."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    nombre: str
    email: str
    rol: str
