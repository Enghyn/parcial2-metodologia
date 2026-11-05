"""Schemas HTTP del módulo agenda (C-04, D6). JSON snake_case (R5).

R1: TODOS los schemas de API declaran `extra="forbid"`.
"""
from __future__ import annotations

from datetime import date, datetime
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

    estado: Literal["reservado", "confirmado", "presente", "atendido", "cancelado", "ausente"]


class ReprogramarTurno(BaseModel):
    """Nuevo horario y duración opcional de un turno (C-09a)."""

    model_config = ConfigDict(extra="forbid")

    inicio: datetime
    duracion_min: int | None = Field(default=None, gt=0)

    @model_validator(mode="before")
    @classmethod
    def _normalizar_fechas(cls, data: object) -> object:
        if isinstance(data, dict):
            data = dict(data)
            if "inicio" in data:
                data["inicio"] = _a_art(data["inicio"])
        return data


class SobreturnoCreate(TurnoCreate):
    """Alta de sobreturno: turno normal + motivo obligatorio (C-09a)."""

    motivo_sobreturno: str = Field(min_length=1, max_length=255)


RANGO_MAX_DIAS: int = 31
"""Máximo de días de calendario que puede abarcar `desde`/`hasta` (C-09b, D2)."""


def _validar_rango(
    fecha: date | None, desde: date | None, hasta: date | None
) -> None:
    """Valida la combinación `fecha` / `desde`+`hasta` del filtro de turnos.

    Reglas de D1/D2: `fecha` y el rango son mutuamente excluyentes, `desde` y
    `hasta` van siempre juntos, `desde <= hasta` y el rango no supera
    `RANGO_MAX_DIAS` días de calendario (ambos extremos incluidos). Levanta
    `ValueError` con el mensaje en español que el borde HTTP devuelve como 422.
    """
    if fecha is not None and (desde is not None or hasta is not None):
        raise ValueError("fecha y el rango desde/hasta son mutuamente excluyentes")
    if (desde is None) != (hasta is None):
        raise ValueError("desde y hasta deben enviarse juntos")
    if desde is not None and hasta is not None:
        if desde > hasta:
            raise ValueError("desde no puede ser posterior a hasta")
        if (hasta - desde).days > RANGO_MAX_DIAS - 1:
            raise ValueError(
                f"El rango no puede superar los {RANGO_MAX_DIAS} días de calendario"
            )


class FiltroTurnos(BaseModel):
    """Filtros de consulta de `GET /api/v1/turnos` (C-09b, D1/D2).

    `fecha` (un día ART) y el rango inclusivo `desde`/`hasta` (días ART) son
    mutuamente excluyentes. `profesional_id` y `sillon_id` acompañan a
    cualquiera de los dos. R1: `extra="forbid"` — el modelo rechaza campos no
    declarados; el query string desconocido lo ignora FastAPI (compatibilidad).
    """

    model_config = ConfigDict(extra="forbid")

    fecha: date | None = None
    desde: date | None = None
    hasta: date | None = None
    profesional_id: UUID | None = None
    sillon_id: UUID | None = None

    @model_validator(mode="after")
    def _validar(self) -> FiltroTurnos:
        _validar_rango(self.fecha, self.desde, self.hasta)
        return self


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
    es_sobreturno: bool
    motivo_sobreturno: str | None
    autorizado_por: UUID | None
    origen: str
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


class SillonOut(BaseModel):
    """Sillón activo del catálogo de la agenda (C-09b: filas de la grilla)."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    nombre: str
    activo: bool


class ProfesionalOut(BaseModel):
    """Profesional activo del catálogo de la agenda (C-09b: filtro y chips)."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    nombre: str


__all__ = [
    "RANGO_MAX_DIAS",
    "BloqueoCreate",
    "BloqueoOut",
    "FiltroTurnos",
    "ProfesionalOut",
    "ReprogramarTurno",
    "SillonOut",
    "SobreturnoCreate",
    "TurnoCreate",
    "TurnoEstadoUpdate",
    "TurnoOut",
]