"""Schemas de ficha clínica (C-07). R1: todos con `extra="forbid"`."""
from __future__ import annotations

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.clinica.models import ESTADOS_PIEZA

EstadoPieza = Literal[
    "sano",
    "caries",
    "obturacion",
    "corona",
    "extraccion",
    "tratamiento_conducto",
]


class PacienteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1, max_length=100)
    dni: str = Field(min_length=1, max_length=20)
    telefono: str = Field(min_length=1, max_length=30)
    email: str | None = Field(default=None, max_length=150)
    obra_social: str | None = Field(default=None, max_length=100)
    nro_afiliado: str | None = Field(default=None, max_length=50)


class PacienteOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    nombre: str
    dni: str
    telefono: str
    email: str | None
    obra_social: str | None
    nro_afiliado: str | None
    activo: bool


class HallazgoIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: EstadoPieza
    observacion: str | None = Field(default=None, max_length=255)
    fecha: date | None = None


class HallazgoOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    pieza: int
    estado: str
    observacion: str | None
    fecha: date


class OdontogramaOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    paciente_id: UUID
    observaciones_generales: str | None
    hallazgos: list[HallazgoOut]


__all__ = [
    "ESTADOS_PIEZA",
    "EstadoPieza",
    "HallazgoIn",
    "HallazgoOut",
    "OdontogramaOut",
    "PacienteCreate",
    "PacienteOut",
]
