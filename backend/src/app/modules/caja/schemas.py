"""Schemas de caja (C-08). R1: todos con `extra="forbid"`."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

TipoMovimiento = Literal["ingreso", "egreso"]
MedioPago = Literal["efectivo", "transferencia", "debito", "credito", "otro"]


class MovimientoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tipo: TipoMovimiento
    medio_pago: MedioPago
    monto: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    concepto: str = Field(min_length=1, max_length=255)
    turno_id: UUID | None = None


class MovimientoOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    fecha: datetime
    tipo: str
    medio_pago: str
    monto: Decimal
    concepto: str
    turno_id: UUID | None
    usuario_id: UUID


class ResumenDiarioOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha: date
    total_ingresos: Decimal
    total_egresos: Decimal
    balance: Decimal
    por_medio_pago: dict[str, Decimal]


__all__ = [
    "MedioPago",
    "MovimientoCreate",
    "MovimientoOut",
    "ResumenDiarioOut",
    "TipoMovimiento",
]
