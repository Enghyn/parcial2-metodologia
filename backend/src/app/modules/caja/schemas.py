"""Schemas de caja (C-08 + C-12). R1: todos con `extra="forbid"`."""
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


# --- C-12: Cierre diario ---

EstadoCierre = Literal["pendiente", "cerrado", "reabierto"]


class CierreCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha_dia: date | None = None  # por defecto: hoy ART


class CierreOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    fecha_dia: date
    estado: EstadoCierre
    balance: Decimal
    total_ingresos: Decimal
    total_egresos: Decimal
    aprobado_por: UUID | None
    aprobado_en: datetime | None
    created_at: datetime


# --- C-12: Cuenta corriente por paciente ---


class MovimientoCuentaCorriente(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    fecha: datetime
    tipo: str
    medio_pago: str
    monto: Decimal
    concepto: str
    usuario_id: UUID


class CuentaCorrienteOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paciente_id: UUID
    saldo: Decimal
    detalle: list[MovimientoCuentaCorriente]


class CuentaCorrienteResumen(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paciente_id: UUID
    nombre: str
    saldo: Decimal


# --- C-12: Ajustes auditados ---


class AjusteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    movimiento_corregido_id: UUID
    motivo: str = Field(min_length=1, max_length=255)
    tipo: TipoMovimiento
    medio_pago: MedioPago
    monto: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    concepto: str = Field(min_length=1, max_length=255)
    turno_id: UUID | None = None


class AjusteOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    movimiento_corregido_id: UUID
    movimiento_ajuste_id: UUID
    motivo: str
    fecha: datetime
    usuario_aprobador_id: UUID
    created_at: datetime


__all__ = [
    "AjusteCreate",
    "AjusteOut",
    "CierreCreate",
    "CierreOut",
    "CuentaCorrienteOut",
    "CuentaCorrienteResumen",
    "EstadoCierre",
    "MedioPago",
    "MovimientoCreate",
    "MovimientoCuentaCorriente",
    "MovimientoOut",
    "ResumenDiarioOut",
    "TipoMovimiento",
]
