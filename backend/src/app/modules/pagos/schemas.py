"""Schemas de pagos (C-17). R1: extra='forbid'."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PagoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    presupuesto_id: UUID | None = None
    monto: float = Field(ge=0)


class PagoOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID
    presupuesto_id: UUID | None
    monto: float
    estado: str
    movimiento_id: UUID | None
    confirmado_en: datetime | None