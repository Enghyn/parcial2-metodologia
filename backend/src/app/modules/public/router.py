"""Router público (C-06, D1/D8): endpoints sin autenticación y validación estricta."""
from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.public.schemas import (
    ProfesionalPublicoOut,
    PublicTurnoOut,
    ReservaCreate,
    SlotOut,
)
from app.modules.public.service import PublicReservaService

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/profesionales", response_model=list[ProfesionalPublicoOut])
def listar_profesionales(db: Annotated[Session, Depends(get_db)]) -> list[ProfesionalPublicoOut]:
    return PublicReservaService(db).listar_profesionales()


@router.get("/disponibilidad", response_model=list[SlotOut])
def consultar_disponibilidad(
    db: Annotated[Session, Depends(get_db)],
    fecha: Annotated[date, Query()],
    duracion_min: Annotated[int, Query(gt=0)] = 30,
    profesional_id: Annotated[UUID | None, Query()] = None,
) -> list[SlotOut]:
    return PublicReservaService(db).disponibilidad(
        fecha=fecha, duracion_min=duracion_min, profesional_id=profesional_id
    )


@router.post("/reservar", response_model=PublicTurnoOut, status_code=status.HTTP_201_CREATED)
def reservar(
    datos: ReservaCreate,
    db: Annotated[Session, Depends(get_db)],
) -> PublicTurnoOut:
    servicio = PublicReservaService(db)
    turno = servicio.reservar(datos)
    return servicio.to_public(turno)


@router.get("/turnos/{token}", response_model=PublicTurnoOut)
def obtener_turno(
    token: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> PublicTurnoOut:
    servicio = PublicReservaService(db)
    return servicio.to_public(servicio.obtener_por_token(token))


@router.post("/turnos/{token}/cancelar", response_model=PublicTurnoOut)
def cancelar_turno(
    token: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> PublicTurnoOut:
    servicio = PublicReservaService(db)
    return servicio.to_public(servicio.cancelar_por_token(token))


__all__ = ["router"]
