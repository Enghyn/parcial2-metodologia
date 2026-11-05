"""Servicio agenda (C-04): helpers puros de solapamiento + TurnoService."""
from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.core.timezone import ahora, fin_dia, inicio_dia, normalizar_entrada
from app.modules.agenda.models import Bloqueo, Profesional, Sillon, Turno
from app.modules.agenda.schemas import (
    BloqueoCreate,
    ReprogramarTurno,
    SobreturnoCreate,
    TurnoCreate,
)
from app.modules.clinica.models import Paciente


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
        desde: date | None = None,
        hasta: date | None = None,
    ) -> list[Turno]:
        """Lista turnos vivos (R13) con orden determinista (D3).

        Filtra por `fecha` (día ART) o por el rango inclusivo `desde`/`hasta`
        en días ART (D1), y opcionalmente por profesional y sillón. Los turnos
        `cancelado` se incluyen: la grilla los muestra atenuados (D5).
        """
        stmt = select(Turno).where(Turno.deleted_at.is_(None))
        if profesional_id is not None:
            stmt = stmt.where(Turno.profesional_id == profesional_id)
        if sillon_id is not None:
            stmt = stmt.where(Turno.sillon_id == sillon_id)
        if fecha is not None:
            if isinstance(fecha, datetime):
                fecha = fecha.date()
            if isinstance(fecha, date):
                stmt = stmt.where(Turno.inicio >= inicio_dia(fecha), Turno.inicio < fin_dia(fecha))
        stmt = self._aplicar_rango(stmt, desde, hasta)
        stmt = stmt.order_by(Turno.inicio, Turno.sillon_id, Turno.id)
        return list(self.db.scalars(stmt))

    @staticmethod
    def _aplicar_rango(
        stmt: Select[Any], desde: date | None, hasta: date | None
    ) -> Select[Any]:
        """Restringe `Turno.inicio` al rango inclusivo de días ART (D1).

        Ambos extremos son días de calendario del consultorio: `desde` aporta
        las 00:00 ART de ese día y `hasta` el inicio del día siguiente (fin
        exclusivo), de modo que un turno a las 23:30 ART del último día entra.
        """
        if desde is not None:
            stmt = stmt.where(Turno.inicio >= inicio_dia(desde))
        if hasta is not None:
            stmt = stmt.where(Turno.inicio < fin_dia(hasta))
        return stmt

    def listar_sillones(self) -> list[Sillon]:
        """Sillones vigentes y activos, por nombre (catálogo de la grilla)."""
        return list(
            self.db.scalars(
                select(Sillon)
                .where(Sillon.deleted_at.is_(None), Sillon.activo.is_(True))
                .order_by(Sillon.nombre)
            )
        )

    def listar_profesionales(self) -> list[Profesional]:
        """Profesionales vigentes y activos, por nombre (filtro y chips)."""
        return list(
            self.db.scalars(
                select(Profesional)
                .where(Profesional.deleted_at.is_(None), Profesional.activo.is_(True))
                .order_by(Profesional.nombre)
            )
        )

    def _recurso_vigente(self, modelo: Any, recurso_id: UUID, nombre: str) -> None:
        recurso = self.db.scalar(
            select(modelo).where(
                modelo.id == recurso_id,
                modelo.deleted_at.is_(None),
                modelo.activo.is_(True),
            )
        )
        if recurso is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{nombre} no encontrado o inactivo",
            )

    def crear(self, datos: TurnoCreate) -> Turno:
        inicio = normalizar_entrada(datos.inicio)
        if inicio <= ahora():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="El turno debe tener un inicio futuro",
            )
        self._recurso_vigente(Sillon, datos.sillon_id, "Sillón")
        self._recurso_vigente(Profesional, datos.profesional_id, "Profesional")
        self._recurso_vigente(Paciente, datos.paciente_id, "Paciente")
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
            es_sobreturno=False,
            motivo_sobreturno=None,
            autorizado_por=None,
        )
        self.db.add(turno)
        self.db.commit()
        self.db.refresh(turno)
        return turno

    def crear_sobreturno(
        self, datos: SobreturnoCreate, autorizado_por: UUID
    ) -> Turno:
        inicio = normalizar_entrada(datos.inicio)
        if inicio <= ahora():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="El turno debe tener un inicio futuro",
            )
        self._recurso_vigente(Sillon, datos.sillon_id, "Sillón")
        self._recurso_vigente(Profesional, datos.profesional_id, "Profesional")
        self._recurso_vigente(Paciente, datos.paciente_id, "Paciente")
        fin = inicio + timedelta(minutes=datos.duracion_min)
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
            es_sobreturno=True,
            motivo_sobreturno=datos.motivo_sobreturno,
            autorizado_por=autorizado_por,
        )
        self.db.add(turno)
        self.db.commit()
        self.db.refresh(turno)
        return turno

    def reprogramar(self, turno_id: UUID, datos: ReprogramarTurno) -> Turno:
        turno = self.db.scalar(
            select(Turno).where(Turno.id == turno_id, Turno.deleted_at.is_(None))
        )
        if turno is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado"
            )
        if turno.estado not in ("reservado", "confirmado"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"No se puede reprogramar un turno en estado {turno.estado}",
            )
        inicio = normalizar_entrada(datos.inicio)
        if inicio <= ahora():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="El turno debe tener un inicio futuro",
            )
        duracion = datos.duracion_min or turno.duracion_min
        fin = inicio + timedelta(minutes=duracion)

        if not turno.es_sobreturno:
            stmt_turnos = select(Turno).where(
                Turno.id != turno.id,
                Turno.deleted_at.is_(None),
                Turno.estado != "cancelado",
                or_(
                    Turno.sillon_id == turno.sillon_id,
                    Turno.profesional_id == turno.profesional_id,
                ),
                Turno.inicio < fin,
                Turno.fin > inicio,
            )
            stmt_bloqueos = select(Bloqueo).where(
                or_(
                    Bloqueo.sillon_id == turno.sillon_id,
                    Bloqueo.profesional_id == turno.profesional_id,
                ),
                Bloqueo.desde < fin,
                Bloqueo.hasta > inicio,
            )
            motivo = detectar_conflicto(
                list(self.db.scalars(stmt_turnos)),
                list(self.db.scalars(stmt_bloqueos)),
                turno.sillon_id,
                turno.profesional_id,
                inicio,
                fin,
            )
            if motivo == "sillon":
                raise HTTPException(
                    status_code=409,
                    detail="Conflicto de agenda: el sillón está ocupado en ese horario",
                )
            if motivo == "profesional":
                raise HTTPException(
                    status_code=409,
                    detail="Conflicto de agenda: el profesional está ocupado en ese horario",
                )
            if motivo == "bloqueo":
                raise HTTPException(
                    status_code=409,
                    detail="Conflicto de agenda: el rango está bloqueado",
                )

        turno.inicio = inicio
        turno.fin = fin
        turno.duracion_min = duracion
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
        desde = normalizar_entrada(datos.desde)
        hasta = normalizar_entrada(datos.hasta)
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


__all__ = ["TurnoService", "detectar_conflicto", "solapamiento"]