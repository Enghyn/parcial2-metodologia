"""Schemas HTTP del módulo agenda (C-04, D6). JSON snake_case (R5).

R1: TODOS los schemas de API declaran `extra="forbid"`.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.timezone import normalizar_entrada


def _a_art(valor: object) -> object:
    if isinstance(valor, datetime):
        return normalizar_entrada(valor)
    return valor


class TurnoCreate(BaseModel):
    """Cuerpo de creación de turno (D6). `fin` se calcula en el servicio."""

    model_config = ConfigDict(extra="forbid")

    paciente_id: UUID
    profesional_id: UUID
    sillon_id: UUID
    prestacion: str = Field(min_length=1, max_length=150)
    inicio: datetime
    duracion_min: int = Field(gt=0)
    sena_monto: Decimal = Field(default=Decimal("0.00"), ge=0)
    notas: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _normalizar_fechas(cls, data: object) -> object:
        if isinstance(data, dict):
            data = dict(data)
            if "inicio" in data:
                data["inicio"] = _a_art(data["inicio"])
        return data


class TurnoEstadoUpdate(BaseModel):
    """Cambio de estado del turno (D6)."""

    model_config = ConfigDict(extra="forbid")

    estado: Literal["reservado", "confirmado", "presente", "atendido", "cancelado"]


class TurnoOut(BaseModel):
    """Representación de salida de un turno (D6)."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    paciente_id: UUID
    profesional_id: UUID
    sillon_id: UUID
    prestacion: str
    inicio: datetime
    fin: datetime
    duracion_min: int
    estado: str
    token_publico: UUID
    sena_monto: Decimal
    notas: str | None
    created_at: datetime
    updated_at: datetime


class BloqueoCreate(BaseModel):
    """Cuerpo de creación de bloqueo (D6)."""

    model_config = ConfigDict(extra="forbid")

    sillon_id: UUID | None = None
    profesional_id: UUID | None = None
    desde: datetime
    hasta: datetime
    motivo: str = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def _normalizar_fechas(cls, data: object) -> object:
        if isinstance(data, dict):
            data = dict(data)
            if "desde" in data:
                data["desde"] = _a_art(data["desde"])
            if "hasta" in data:
                data["hasta"] = _a_art(data["hasta"])
        return data

    @model_validator(mode="after")
    def _validar(self) -> BloqueoCreate:
        if self.sillon_id is None and self.profesional_id is None:
            raise ValueError("Debe indicar sillon_id o profesional_id")
        if self.hasta <= self.desde:
            raise ValueError("hasta debe ser mayor que desde")
        return self


class BloqueoOut(BaseModel):
    """Representación de salida de un bloqueo (D6)."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    sillon_id: UUID | None
    profesional_id: UUID | None
    desde: datetime
    hasta: datetime
    motivo: str
    created_at: datetime
    updated_at: datetime


__all__ = [
    "BloqueoCreate",
    "BloqueoOut",
    "TurnoCreate",
    "TurnoEstadoUpdate",
    "TurnoOut",
]