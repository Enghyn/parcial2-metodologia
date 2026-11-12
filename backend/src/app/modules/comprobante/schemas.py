"""Schemas de comprobante (C-13b). R1: extra='forbid'."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ComprobanteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    numero: str = Field(min_length=1, max_length=50)
    movimiento_id: UUID | None = None
    presupuesto_id: UUID | None = None


class ComprobanteOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID
    numero: str
    movimiento_id: UUID | None
    presupuesto_id: UUID | None
    estado: str
    emitido_por: UUID | None
    emitido_en: datetime | None
    anulado_en: datetime | None