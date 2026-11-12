"""Schemas de presupuestos (C-16). R1: extra='forbid'."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    descripcion: str = Field(min_length=1, max_length=255)
    cantidad: int = Field(ge=1, default=1)
    arancel: float = Field(ge=0)
    copago: float = Field(ge=0, default=0)


class PresupuestoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    paciente_id: UUID
    items: list[ItemCreate] = Field(min_length=1)


class PresupuestoOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID
    paciente_id: UUID
    estado: str
    total: float
    token_publico: UUID
    aprobado_en: datetime | None