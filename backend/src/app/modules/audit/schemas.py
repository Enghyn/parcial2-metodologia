"""Schemas Pydantic del visor y export de auditoría (R1: extra='forbid')."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditoriaOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    fecha: datetime
    usuario_id: UUID | None
    accion: str
    recurso: str
    recurso_id: UUID | None
    diff: dict[str, Any] | None
    ip: str | None
    user_agent: str | None


__all__ = ["AuditoriaOut"]
