"""Servicios de ficha clínica (C-07): pacientes y odontograma FDI."""
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.timezone import ahora
from app.modules.clinica.models import HallazgoPieza, Odontograma, Paciente
from app.modules.clinica.schemas import HallazgoIn, PacienteCreate


def _validar_pieza(pieza: int) -> None:
    if not (11 <= pieza <= 48 and 1 <= pieza % 10 <= 8):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Pieza FDI inválida: usá 11–18, 21–28, 31–38 o 41–48",
        )


class PacienteService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def listar(self, q: str | None = None) -> list[Paciente]:
        stmt = select(Paciente).where(Paciente.deleted_at.is_(None))
        if q:
            patron = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(Paciente.nombre.ilike(patron), Paciente.dni.ilike(patron))
            )
        return list(self.db.scalars(stmt.order_by(Paciente.nombre)))

    def crear(self, datos: PacienteCreate) -> Paciente:
        existente = self.db.scalar(select(Paciente).where(Paciente.dni == datos.dni))
        if existente is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un paciente con ese DNI",
            )
        paciente = Paciente(**datos.model_dump(), activo=True)
        self.db.add(paciente)
        try:
            self.db.commit()
        except IntegrityError:
            # Carrera entre el chequeo y el INSERT: el UNIQUE(dni) manda.
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un paciente con ese DNI",
            ) from None
        self.db.refresh(paciente)
        return paciente


class OdontogramaService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _paciente_vigente(self, paciente_id: UUID) -> Paciente:
        paciente = self.db.scalar(
            select(Paciente).where(
                Paciente.id == paciente_id, Paciente.deleted_at.is_(None)
            )
        )
        if paciente is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado"
            )
        return paciente

    def obtener_o_crear(self, paciente_id: UUID) -> Odontograma:
        self._paciente_vigente(paciente_id)
        odontograma = self.db.scalar(
            select(Odontograma).where(Odontograma.paciente_id == paciente_id)
        )
        if odontograma is None:
            # Upsert atómico: dos GET concurrentes no chocan con UNIQUE(paciente_id).
            self.db.execute(
                pg_insert(Odontograma)
                .values(paciente_id=paciente_id)
                .on_conflict_do_nothing(index_elements=["paciente_id"])
            )
            self.db.commit()
            odontograma = self.db.scalar(
                select(Odontograma).where(Odontograma.paciente_id == paciente_id)
            )
            if odontograma is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="No se pudo crear el odontograma",
                )
        return odontograma

    def listar_hallazgos(self, odontograma_id: UUID) -> list[HallazgoPieza]:
        return list(
            self.db.scalars(
                select(HallazgoPieza)
                .where(HallazgoPieza.odontograma_id == odontograma_id)
                .order_by(HallazgoPieza.pieza)
            )
        )

    def upsert(self, paciente_id: UUID, pieza: int, datos: HallazgoIn) -> HallazgoPieza:
        _validar_pieza(pieza)
        odontograma = self.obtener_o_crear(paciente_id)
        hallazgo = self.db.scalar(
            select(HallazgoPieza).where(
                HallazgoPieza.odontograma_id == odontograma.id,
                HallazgoPieza.pieza == pieza,
            )
        )
        if hallazgo is None:
            hallazgo = HallazgoPieza(
                odontograma_id=odontograma.id,
                pieza=pieza,
                estado=datos.estado,
                observacion=datos.observacion,
                fecha=datos.fecha or ahora().date(),
            )
            self.db.add(hallazgo)
        else:
            hallazgo.estado = datos.estado
            hallazgo.observacion = datos.observacion
            if datos.fecha is not None:
                hallazgo.fecha = datos.fecha
        self.db.commit()
        self.db.refresh(hallazgo)
        return hallazgo


__all__ = ["OdontogramaService", "PacienteService"]
