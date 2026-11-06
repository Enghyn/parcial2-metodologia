"""Schemas de ficha clínica (C-07) y ficha clínica avanzada (C-11). R1: todos con `extra="forbid"`."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
    autor_usuario_id: UUID | None = None


class EvolucionCreate(BaseModel):
    """Datos para alta de evolución clínica (C-11, D3). autor y fecha los pone el servidor.
    paciente_id viene de la URL del path, no del body."""

    model_config = ConfigDict(extra="forbid")

    paciente_id: UUID | None = None
    texto: str = Field(min_length=1, max_length=4000)

    @field_validator("texto")
    @classmethod
    def _texto_no_vacio(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("El texto de la evolución no puede estar vacío")
        return valor


class EvolucionOut(BaseModel):
    """Vista de evolución clínica (C-11, D3)."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    paciente_id: UUID
    autor_usuario_id: UUID
    fecha: datetime
    texto: str


class ConsentimientoCreate(BaseModel):
    """Datos para alta de consentimiento informado (C-11, D4). autor y fecha los pone el servidor.
    paciente_id viene de la URL del path, no del body."""

    model_config = ConfigDict(extra="forbid")

    paciente_id: UUID | None = None
    version: str = Field(min_length=1, max_length=20)

    @field_validator("version")
    @classmethod
    def _version_no_vacia(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("La versión del consentimiento no puede estar vacía")
        return valor


class ConsentimientoOut(BaseModel):
    """Vista de consentimiento informado (C-11, D4)."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    paciente_id: UUID
    version: str
    fecha: datetime
    autor_usuario_id: UUID


class OdontogramaOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    paciente_id: UUID
    observaciones_generales: str | None
    hallazgos: list[HallazgoOut]


class HistorialPiezaOut(BaseModel):
    """Vista del historial de cambios de una pieza (C-11, tarea 6)."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    estado_anterior: str | None
    estado_nuevo: str
    observacion_anterior: str | None
    observacion_nueva: str | None
    registrado_en: datetime
    registrado_por: UUID | None


__all__ = [
    "ConsentimientoCreate",
    "ConsentimientoOut",
    "EvolucionCreate",
    "EvolucionOut",
    "ESTADOS_PIEZA",
    "EstadoPieza",
    "HallazgoIn",
    "HallazgoOut",
    "HistorialPiezaOut",
    "OdontogramaOut",
    "PacienteCreate",
    "PacienteOut",
]
