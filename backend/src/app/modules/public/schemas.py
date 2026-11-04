"""Schemas HTTP del módulo público (C-06, D7). JSON snake_case (R5).

R1: TODOS los schemas de API declaran `extra="forbid"`.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PacientePublicoIn(BaseModel):
    """Datos mínimos del paciente para reservar sin login (D7)."""

    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1, max_length=100)
    dni: str = Field(min_length=1, max_length=20)
    telefono: str = Field(min_length=1, max_length=30)
    email: str | None = Field(default=None, max_length=150)


class ReservaCreate(BaseModel):
    """Cuerpo de reserva pública (D7). `fin` se calcula en el servicio."""

    model_config = ConfigDict(extra="forbid")

    prestacion: str = Field(min_length=1, max_length=150)
    duracion_min: int = Field(gt=0)
    inicio: datetime
    profesional_id: UUID
    sillon_id: UUID
    paciente: PacientePublicoIn

    @field_validator("inicio")
    @classmethod
    def _normalizar_inicio(cls, valor: datetime) -> datetime:
        if valor.tzinfo is None:
            return valor.replace(tzinfo=timezone.utc)
        return valor


class SlotOut(BaseModel):
    """Hueco libre con profesional y sillón asignados (D7)."""

    model_config = ConfigDict(extra="forbid")

    inicio: datetime
    profesional_id: UUID
    sillon_id: UUID


class ProfesionalPublicoOut(BaseModel):
    """Profesional visible en el portal público (D9)."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    nombre: str


class PublicTurnoOut(BaseModel):
    """Vista pública de un turno: sin IDs internos ni datos sensibles (D6/R9)."""

    model_config = ConfigDict(extra="forbid")

    token: UUID
    prestacion: str
    inicio: datetime
    fin: datetime
    duracion_min: int
    estado: str
    paciente_nombre: str
    profesional_nombre: str
    sillon_nombre: str


__all__ = [
    "PacientePublicoIn",
    "ProfesionalPublicoOut",
    "PublicTurnoOut",
    "ReservaCreate",
    "SlotOut",
]
