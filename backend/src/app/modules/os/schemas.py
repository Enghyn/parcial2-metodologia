"""Schemas de OS/convenios/afiliación (C-13a). R1: extra='forbid'."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ObraSocialCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str = Field(min_length=1, max_length=100)
    codigo: str | None = None
    activo: bool = True


class ObraSocialOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID
    nombre: str
    codigo: str | None
    activo: bool


class ConvenioCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    obra_social_id: UUID
    nombre: str = Field(min_length=1, max_length=100)
    vigente_desde: date
    vigente_hasta: date | None = None
    descuento_global: float | None = None
    activo: bool = True


class ConvenioOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID
    obra_social_id: UUID
    nombre: str
    vigente_desde: date
    vigente_hasta: date | None
    descuento_global: float | None
    activo: bool


class AfiliacionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    paciente_id: UUID
    obra_social_id: UUID
    convenio_id: UUID | None = None
    nro_afiliado: str | None = None
    vigente_desde: date
    vigente_hasta: date | None = None


class AfiliacionOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID
    paciente_id: UUID
    obra_social_id: UUID
    convenio_id: UUID | None
    nro_afiliado: str | None
    vigente_desde: date
    vigente_hasta: date | None