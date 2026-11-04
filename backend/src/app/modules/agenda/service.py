"""Servicio agenda (C-04): helpers puros de solapamiento + TurnoService."""
from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.modules.agenda.models import Bloqueo, Turno
from app.modules.agenda.schemas import BloqueoCreate, TurnoCreate


def solapamiento(inicio_a: datetime, fin_a: datetime, inicio_b: datetime, fin_b: datetime) -> bool:
    """Fórmula exacta RN-AG-01."""
    return inicio_a < fin_b and fin_a > inicio_b


def detectar_conflicto(
    turnos: Iterable[Turno],
    bloqueos: Iterable[Bloqueo],
    sillon_id: UUID,
    profesional_id: UUID,
    inicio: datetime,
    fin: datetime,
) -> str | None:
    turnos_activos = [
        t for t in turnos if t.deleted_at is None and t.estado != "cancelado"
    ]

    conflicto_sillon = False
    conflicto_profesional = False
    for turno in turnos_activos:
        if not solapamiento(turno.inicio, turno.fin, inicio, fin):
            continue
        if turno.sillon_id == sillon_id:
            conflicto_sillon = True
        if turno.profesional_id == profesional_id:
            conflicto_profesional = True

    if conflicto_sillon:
        return "sillon"
    if conflicto_profesional:
        return "profesional"

    for bloqueo in bloqueos:
        if not solapamiento(bloqueo.desde, bloqueo.hasta, inicio, fin):
            continue
        if bloqueo.sillon_id == sillon_id or bloqueo.profesional_id == profesional_id:
            return "bloqueo"

    return None


class TurnoService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def listar(
        self,
        fecha: Any = None,
        profesional_id: UUID | None = None,
        sillon_id: UUID | None = None,
    ) -> list[Turno]:
        stmt = select(Turno).where(Turno.deleted_at.is_(None))
        if profesional_id is not None:
            stmt = stmt.where(Turno.profesional_id == profesional_id)
        if sillon_id is not None:
            stmt = stmt.where(Turno.sillon_id == sillon_id)
        if fecha is not None:
            if isinstance(fecha, datetime):
                fecha = fecha.date()
            if isinstance(fecha, date):
                start = datetime.combine(fecha, time.min, tzinfo=timezone.utc)
                end = start + timedelta(days=1)
                stmt = stmt.where(Turno.inicio >= start, Turno.inicio < end)
        stmt = stmt.order_by(Turno.inicio)
        return list(self.db.scalars(stmt))

    def crear(self, datos: TurnoCreate) -> Turno:
        inicio = datos.inicio
        if inicio.tzinfo is None:
            inicio = inicio.replace(tzinfo=timezone.utc)
        fin = inicio + timedelta(minutes=datos.duracion_min)

        stmt_turnos = select(Turno).where(
            Turno.deleted_at.is_(None),
            Turno.estado != "cancelado",
            or_(Turno.sillon_id == datos.sillon_id, Turno.profesional_id == datos.profesional_id),
            Turno.inicio < fin,
            Turno.fin > inicio,
        )
        turnos = list(self.db.scalars(stmt_turnos))

        stmt_bloqueos = select(Bloqueo).where(
            or_(Bloqueo.sillon_id == datos.sillon_id, Bloqueo.profesional_id == datos.profesional_id),
            Bloqueo.desde < fin,
            Bloqueo.hasta > inicio,
        )
        bloqueos = list(self.db.scalars(stmt_bloqueos))

        motivo = detectar_conflicto(turnos, bloqueos, datos.sillon_id, datos.profesional_id, inicio, fin)
        if motivo == "sillon":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflicto de agenda: el sillón está ocupado en ese horario")
        if motivo == "profesional":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflicto de agenda: el profesional está ocupado en ese horario")
        if motivo == "bloqueo":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflicto de agenda: el rango está bloqueado")

        turno = Turno(
            paciente_id=datos.paciente_id,
            profesional_id=datos.profesional_id,
            sillon_id=datos.sillon_id,
            prestacion=datos.prestacion,
            inicio=inicio,
            fin=fin,
            duracion_min=datos.duracion_min,
            estado="reservado",
            sena_monto=datos.sena_monto,
            notas=datos.notas,
        )
        self.db.add(turno)
        self.db.commit()
        self.db.refresh(turno)
        return turno

    def cambiar_estado(self, turno_id: UUID, estado: str) -> Turno:
        turno = self.db.scalar(select(Turno).where(Turno.id == turno_id, Turno.deleted_at.is_(None)))
        if turno is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado")
        turno.estado = estado
        self.db.commit()
        self.db.refresh(turno)
        return turno

    def crear_bloqueo(self, datos: BloqueoCreate) -> Bloqueo:
        desde = datos.desde
        hasta = datos.hasta
        if desde.tzinfo is None:
            desde = desde.replace(tzinfo=timezone.utc)
        if hasta.tzinfo is None:
            hasta = hasta.replace(tzinfo=timezone.utc)
        bloqueo = Bloqueo(
            sillon_id=datos.sillon_id,
            profesional_id=datos.profesional_id,
            desde=desde,
            hasta=hasta,
            motivo=datos.motivo,
        )
        self.db.add(bloqueo)
        self.db.commit()
        self.db.refresh(bloqueo)
        return bloqueo

    def eliminar_bloqueo(self, bloqueo_id: UUID) -> None:
        bloqueo = self.db.scalar(select(Bloqueo).where(Bloqueo.id == bloqueo_id))
        if bloqueo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bloqueo no encontrado")
        self.db.delete(bloqueo)
        self.db.commit()


__all__ = ["solapamiento", "detectar_conflicto", "TurnoService"]