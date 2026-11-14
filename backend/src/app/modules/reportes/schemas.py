"""Schemas de reportes (C-21). R1: todos con `extra="forbid"`."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

EstadoTurno = Literal["reservado", "confirmado", "presente", "atendido", "cancelado", "ausente"]
MedioPago = Literal["efectivo", "transferencia", "debito", "credito", "otro"]


class ReporteRangoIn(BaseModel):
    """Filtro de rango de fechas para reportes (D2).

    `desde` y `hasta` son opcionales y van juntos; el servicio aplica el
    default de los ultimos 30 dias ART cuando faltan. R1: `extra="forbid"`.
    """

    model_config = ConfigDict(extra="forbid")

    desde: date | None = None
    hasta: date | None = None
    profesional_id: UUID | None = None
    sillon_id: UUID | None = None

    @model_validator(mode="after")
    def _validar_rango(self) -> ReporteRangoIn:
        """Rechaza con ValueError (-> 422 HTTP) cuando `desde > hasta`."""
        if self.desde is not None and self.hasta is not None and self.desde > self.hasta:
            raise ValueError("desde no puede ser posterior a hasta")
        return self


class OcupacionRecursoOut(BaseModel):
    """Fila de ocupacion por recurso (sillon o profesional)."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    nombre: str
    reservado: int = Field(ge=0)
    confirmado: int = Field(ge=0)
    presente: int = Field(ge=0)
    atendido: int = Field(ge=0)
    cancelado: int = Field(ge=0)
    tasa_ocupacion: float = Field(ge=0, le=1)
    horas_bloqueadas: float = Field(ge=0)


class OcupacionOut(BaseModel):
    """Respuesta de GET /reportes/ocupacion."""

    model_config = ConfigDict(extra="forbid")

    desde: date
    hasta: date
    sillones: list[OcupacionRecursoOut]
    profesionales: list[OcupacionRecursoOut]


class FacturacionMedioOut(BaseModel):
    """Total facturado por medio de pago."""

    model_config = ConfigDict(extra="forbid")

    medio_pago: str
    total: Decimal = Field(ge=0)


class FacturacionOSOut(BaseModel):
    """Desglose por obra social (monto OS, copago, total del paciente)."""

    model_config = ConfigDict(extra="forbid")

    obra_social: str
    monto_os: Decimal = Field(ge=0)
    copago_paciente: Decimal = Field(ge=0)
    total_paciente: Decimal = Field(ge=0)


class FacturacionOut(BaseModel):
    """Respuesta de GET /reportes/facturacion."""

    model_config = ConfigDict(extra="forbid")

    desde: date
    hasta: date
    por_medio_pago: list[FacturacionMedioOut]
    total_ingresos: Decimal = Field(ge=0)
    balance_neto: Decimal = Field(ge=0)
    por_obra_social: list[FacturacionOSOut]


class AusentismoTurnoOut(BaseModel):
    """Turno ausente (cancelado / no presentado) para detalle de export."""

    model_config = ConfigDict(extra="forbid")

    turno_id: UUID
    inicio: datetime
    estado: EstadoTurno
    profesional_id: UUID
    sillon_id: UUID


class AusentismoOut(BaseModel):
    """Respuesta de GET /reportes/ausentismo."""

    model_config = ConfigDict(extra="forbid")

    desde: date
    hasta: date
    cancelados: int = Field(ge=0)
    no_presentados: int = Field(ge=0)
    recuperados: int = Field(ge=0)
    tasa_ausentismo: float = Field(ge=0, le=1)
    total_turnos: int = Field(ge=0)


__all__ = [
    "AusentismoOut",
    "AusentismoTurnoOut",
    "EstadoTurno",
    "FacturacionMedioOut",
    "FacturacionOSOut",
    "FacturacionOut",
    "MedioPago",
    "OcupacionOut",
    "OcupacionRecursoOut",
    "ReporteRangoIn",
]
