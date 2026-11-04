"""Servicio público de reserva (C-06, D2/D3/D4/D5).

Reusa `TurnoService` y los helpers de solapamiento de C-04 (R6): la validación
antisolapamiento vive en un único lugar. Los helpers `generar_inicios` y
`slot_libre` son puros para poder testearlos sin DB.
"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, time, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.timezone import ahora, combinar, fin_dia, inicio_dia
from app.modules.agenda.models import Bloqueo, Profesional, Sillon, Turno
from app.modules.agenda.schemas import TurnoCreate
from app.modules.agenda.service import TurnoService, solapamiento
from app.modules.clinica.models import Paciente
from app.modules.public.schemas import (
    PacientePublicoIn,
    ProfesionalPublicoOut,
    PublicTurnoOut,
    ReservaCreate,
    SlotOut,
)

_ESTADOS_CANCELABLES = ("reservado", "confirmado")


def _minutos(valor: time) -> int:
    return valor.hour * 60 + valor.minute


def _hora(minutos: int) -> time:
    return time(hour=minutos // 60, minute=minutos % 60)


def _parse_hora(valor: str, default: time) -> time:
    try:
        horas, minutos = valor.split(":")
        return time(int(horas), int(minutos))
    except (AttributeError, ValueError):
        return default


def generar_inicios(start: time, end: time, grid_min: int, duracion_min: int) -> list[time]:
    """Inicios candidatos de la jornada para una duración dada (D3, puro)."""
    if grid_min <= 0 or duracion_min <= 0:
        return []
    desde = _minutos(start)
    hasta = _minutos(end)
    inicios: list[time] = []
    actual = desde
    while actual + duracion_min <= hasta:
        inicios.append(_hora(actual))
        actual += grid_min
    return inicios


def slot_libre(
    turnos: Iterable[Turno],
    bloqueos: Iterable[Bloqueo],
    sillon_id: UUID,
    profesional_id: UUID,
    inicio: datetime,
    fin: datetime,
) -> bool:
    """True si el rango está libre para ese sillón y profesional (D3, puro).

    Reusa la fórmula RN-AG-01 (`solapamiento`) y excluye turnos cancelados o
    con borrado lógico (R13).
    """
    for turno in turnos:
        if turno.deleted_at is not None or turno.estado == "cancelado":
            continue
        if not solapamiento(turno.inicio, turno.fin, inicio, fin):
            continue
        if turno.sillon_id == sillon_id or turno.profesional_id == profesional_id:
            return False

    for bloqueo in bloqueos:
        if not solapamiento(bloqueo.desde, bloqueo.hasta, inicio, fin):
            continue
        if bloqueo.sillon_id == sillon_id or bloqueo.profesional_id == profesional_id:
            return False

    return True


class PublicReservaService:
    """Orquesta disponibilidad, reserva, consulta y cancelación por token."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def disponibilidad(
        self,
        fecha: date,
        duracion_min: int,
        profesional_id: UUID | None = None,
    ) -> list[SlotOut]:
        settings = get_settings()
        start = _parse_hora(settings.public_slot_start, time(8, 0))
        end = _parse_hora(settings.public_slot_end, time(20, 0))
        grid = settings.public_slot_grid_min if settings.public_slot_grid_min > 0 else 30
        inicios = generar_inicios(start, end, grid, duracion_min)

        day_start = inicio_dia(fecha)
        day_end = fin_dia(fecha)

        profesionales = list(
            self.db.scalars(
                select(Profesional)
                .where(Profesional.deleted_at.is_(None), Profesional.activo.is_(True))
                .order_by(Profesional.nombre)
            )
        )
        if profesional_id is not None:
            profesionales = [p for p in profesionales if p.id == profesional_id]

        sillones = list(
            self.db.scalars(
                select(Sillon)
                .where(Sillon.deleted_at.is_(None), Sillon.activo.is_(True))
                .order_by(Sillon.nombre)
            )
        )

        turnos = list(
            self.db.scalars(
                select(Turno).where(
                    Turno.deleted_at.is_(None),
                    Turno.estado != "cancelado",
                    Turno.inicio < day_end,
                    Turno.fin > day_start,
                )
            )
        )
        bloqueos = list(
            self.db.scalars(
                select(Bloqueo).where(Bloqueo.desde < day_end, Bloqueo.hasta > day_start)
            )
        )

        slots: list[SlotOut] = []
        for profesional in profesionales:
            for hora in inicios:
                inicio = combinar(fecha, hora)
                if inicio <= ahora():
                    continue
                fin = inicio + timedelta(minutes=duracion_min)
                for sillon in sillones:
                    if slot_libre(turnos, bloqueos, sillon.id, profesional.id, inicio, fin):
                        slots.append(
                            SlotOut(
                                inicio=inicio,
                                profesional_id=profesional.id,
                                sillon_id=sillon.id,
                            )
                        )
                        break

        slots.sort(key=lambda s: (s.inicio, str(s.profesional_id)))
        return slots

    def listar_profesionales(self) -> list[ProfesionalPublicoOut]:
        profesionales = self.db.scalars(
            select(Profesional)
            .where(Profesional.deleted_at.is_(None), Profesional.activo.is_(True))
            .order_by(Profesional.nombre)
        )
        return [
            ProfesionalPublicoOut(id=p.id, nombre=p.nombre) for p in profesionales
        ]

    def _find_or_create_paciente(self, datos: PacientePublicoIn) -> Paciente:
        paciente = self.db.scalar(
            select(Paciente).where(
                Paciente.dni == datos.dni, Paciente.deleted_at.is_(None)
            )
        )
        if paciente is not None:
            # R9/privacidad: el portal anónimo no puede sobrescribir datos ajenos.
            return paciente

        borrado = self.db.scalar(select(Paciente).where(Paciente.dni == datos.dni))
        if borrado is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El DNI figura en una ficha dada de baja. Contactá al consultorio para actualizarla.",
            )

        paciente = Paciente(
            nombre=datos.nombre,
            dni=datos.dni,
            telefono=datos.telefono,
            email=datos.email,
        )
        self.db.add(paciente)
        self.db.flush()
        return paciente

    def reservar(self, datos: ReservaCreate) -> Turno:
        paciente = self._find_or_create_paciente(datos.paciente)
        turno_create = TurnoCreate(
            paciente_id=paciente.id,
            profesional_id=datos.profesional_id,
            sillon_id=datos.sillon_id,
            prestacion=datos.prestacion,
            inicio=datos.inicio,
            duracion_min=datos.duracion_min,
        )
        # R6: la validación antisolapamiento vive en TurnoService.
        return TurnoService(self.db).crear(turno_create)

    def obtener_por_token(self, token: UUID) -> Turno:
        turno = self.db.scalar(
            select(Turno).where(
                Turno.token_publico == token, Turno.deleted_at.is_(None)
            )
        )
        if turno is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado"
            )
        return turno

    def cancelar_por_token(self, token: UUID) -> Turno:
        turno = self.obtener_por_token(token)
        if turno.estado not in _ESTADOS_CANCELABLES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"No se puede cancelar un turno en estado {turno.estado}",
            )
        turno.estado = "cancelado"
        self.db.commit()
        self.db.refresh(turno)
        return turno

    def to_public(self, turno: Turno) -> PublicTurnoOut:
        paciente = self.db.get(Paciente, turno.paciente_id)
        profesional = self.db.get(Profesional, turno.profesional_id)
        sillon = self.db.get(Sillon, turno.sillon_id)
        return PublicTurnoOut(
            token=turno.token_publico,
            prestacion=turno.prestacion,
            inicio=turno.inicio,
            fin=turno.fin,
            duracion_min=turno.duracion_min,
            estado=turno.estado,
            paciente_nombre=paciente.nombre if paciente is not None else "",
            profesional_nombre=profesional.nombre if profesional is not None else "",
            sillon_nombre=sillon.nombre if sillon is not None else "",
        )


__all__ = ["PublicReservaService", "generar_inicios", "slot_libre"]
