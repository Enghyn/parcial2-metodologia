"""Schemas de admin (C-19). R1: extra='forbid'."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UsuarioCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=6, max_length=128)
    rol: str
    activo: bool = True


class UsuarioOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID
    nombre: str
    email: str
    rol: str
    activo: bool


class SillonCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str = Field(min_length=1, max_length=50)
    descripcion: str | None = None
    activo: bool = True


class SillonOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID
    nombre: str
    descripcion: str | None
    activo: bool


class ProfesionalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str = Field(min_length=1, max_length=100)
    matricula: str = Field(min_length=1, max_length=50)
    especialidad: str | None = None
    duracion_default_min: int = 30
    usuario_id: UUID | None = None
    activo: bool = True


class ProfesionalOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID
    nombre: str
    matricula: str
    especialidad: str | None
    duracion_default_min: int
    usuario_id: UUID | None
    activo: bool