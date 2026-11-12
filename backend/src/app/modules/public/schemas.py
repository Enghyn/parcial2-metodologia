"""Schemas HTTP del módulo público (C-06, D7). JSON snake_case (R5).

R1: TODOS los schemas de API declaran `extra="forbid"`.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.timezone import normalizar_entrada


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
    pre_reserva_token: UUID | None = None

    @field_validator("inicio")
    @classmethod
    def _normalizar_inicio(cls, valor: datetime) -> datetime:
        return normalizar_entrada(valor)


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


class PreReservaCreate(BaseModel):
    """Cuerpo de retención de hueco (C-10, D1). Sin datos de paciente (R9)."""

    model_config = ConfigDict(extra="forbid")

    prestacion: str = Field(min_length=1, max_length=150)
    duracion_min: int = Field(gt=0)
    inicio: datetime
    profesional_id: UUID
    sillon_id: UUID

    @field_validator("inicio")
    @classmethod
    def _normalizar_inicio(cls, valor: datetime) -> datetime:
        return normalizar_entrada(valor)


class PreReservaOut(BaseModel):
    """Vista pública de una retención (C-10, D2)."""

    model_config = ConfigDict(extra="forbid")

    pre_reserva_token: UUID
    inicio: datetime
    fin: datetime
    duracion_min: int
    expira_en: datetime


class ReprogramarPublico(BaseModel):
    """Reprogramación pública: solo `inicio` (D6)."""

    model_config = ConfigDict(extra="forbid")

    inicio: datetime

    @field_validator("inicio")
    @classmethod
    def _normalizar_inicio(cls, valor: datetime) -> datetime:
        return normalizar_entrada(valor)


# --- Portal público de presupuestos y pagos (C-18, D5) ---
# R9: los contratos públicos omiten `id`, `paciente_id`, `presupuesto_id`,
# `movimiento_id` y `token_publico`; nunca exponen PII ni datos clínicos.


class ItemPresupuestoPublicoOut(BaseModel):
    """Ítem visible en la vista pública del presupuesto (D5)."""

    model_config = ConfigDict(extra="forbid")

    descripcion: str
    cantidad: int
    arancel: float
    copago: float


class PresupuestoPublicoOut(BaseModel):
    """Vista pública mínima del presupuesto: estado, total e ítems (D5/R9)."""

    model_config = ConfigDict(extra="forbid")

    estado: str
    total: float
    items: list[ItemPresupuestoPublicoOut]


class PagoPublicoOut(BaseModel):
    """Vista pública del pago simulado: estado, monto y fecha (D5/R9)."""

    model_config = ConfigDict(extra="forbid")

    estado: str
    monto: float
    confirmado_en: datetime | None


class AprobacionPublicaIn(BaseModel):
    """Firma simple del paciente para aprobar un presupuesto (D5)."""

    model_config = ConfigDict(extra="forbid")

    firma: str = Field(min_length=1, max_length=150)


class RechazoPublicoIn(BaseModel):
    """Motivo opcional al rechazar un presupuesto desde el portal (D5)."""

    model_config = ConfigDict(extra="forbid")

    motivo: str | None = Field(default=None, max_length=255)


class ConfirmarPublicoIn(BaseModel):
    """Cuerpo opcional para confirmar pago público (C-18, R1).

    Declara ``extra="forbid"`` para que un body con campos no esperados responda 422.
    El body es opcional: ``None`` o ``{}`` mantienen compatibilidad; cualquier campo
    no declarado devuelve 422.
    """

    model_config = ConfigDict(extra="forbid")


__all__ = [
    "AprobacionPublicaIn",
    "ItemPresupuestoPublicoOut",
    "PacientePublicoIn",
    "PagoPublicoOut",
    "PreReservaCreate",
    "PreReservaOut",
    "PresupuestoPublicoOut",
    "ProfesionalPublicoOut",
    "PublicTurnoOut",
    "RechazoPublicoIn",
    "ReprogramarPublico",
    "ReservaCreate",
    "SlotOut",
]
