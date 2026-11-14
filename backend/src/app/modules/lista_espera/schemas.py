"""Schemas de lista de espera (C-15). R1: extra='forbid'."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ListaEsperaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    paciente_id: UUID
    profesional_id: UUID | None = None
    sillon_id: UUID | None = None
    fecha_preferida: datetime | None = None


class ListaEsperaOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID
    paciente_id: UUID
    profesional_id: UUID | None
    sillon_id: UUID | None
    fecha_preferida: datetime | None
    estado: str
    ofrecido_en: datetime | None
    expira_en: datetime | None