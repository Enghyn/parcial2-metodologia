"""Schemas de nomenclador (C-13a). R1: extra='forbid'."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PracticaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    codigo: str = Field(min_length=1, max_length=50)
    descripcion: str = Field(min_length=1, max_length=255)
    arancel_base: float = Field(ge=0)


class PracticaOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID
    codigo: str
    descripcion: str
    arancel_base: float


class ConvenioPracticaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    convenio_id: UUID
    practica_id: UUID
    arancel_override: float | None = None
    copago_fijo: float | None = None
    copago_porcentaje: float | None = None


class ConvenioPracticaOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID
    convenio_id: UUID
    practica_id: UUID
    arancel_override: float | None
    copago_fijo: float | None
    copago_porcentaje: float | None