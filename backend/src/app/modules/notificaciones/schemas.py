"""Schemas de notificaciones (C-14). R1: extra='forbid'."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificacionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    turno_id: UUID | None = None
    plantilla: str = Field(min_length=1, max_length=50)
    destinatario: str = Field(min_length=1, max_length=100)


class NotificacionOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID
    turno_id: UUID | None
    plantilla: str
    destinatario: str
    estado: str
    enviado_en: datetime | None