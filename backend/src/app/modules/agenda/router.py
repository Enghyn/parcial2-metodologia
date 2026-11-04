"""Router agenda (C-04): endpoints de turnos y bloqueos con RBAC (D7/D8)."""
from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.session import get_db
from app.modules.agenda.schemas import (
    BloqueoCreate,
    BloqueoOut,
    TurnoCreate,
    TurnoEstadoUpdate,
    TurnoOut,
)
from app.modules.agenda.service import TurnoService

router = APIRouter(tags=["agenda"])


def _servicio(db: Session) -> TurnoService:
    return TurnoService(db)


@router.get(
    "/turnos",
    response_model=list[TurnoOut],
    dependencies=[Depends(require_role("admin", "recepcion", "odontologo"))],
)
def listar_turnos(
    db: Annotated[Session, Depends(get_db)],
    fecha: Annotated[date | None, Query()] = None,
    profesional_id: Annotated[UUID | None, Query()] = None,
    sillon_id: Annotated[UUID | None, Query()] = None,
) -> list[TurnoOut]:
    servicio = TurnoService(db)
    turnos = servicio.listar(fecha=fecha, profesional_id=profesional_id, sillon_id=sillon_id)
    return [TurnoOut.model_validate(t) for t in turnos]


@router.post(
    "/turnos",
    response_model=TurnoOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "recepcion"))],
)
def crear_turno(
    datos: TurnoCreate,
    db: Annotated[Session, Depends(get_db)],
) -> TurnoOut:
    servicio = TurnoService(db)
    turno = servicio.crear(datos)
    return TurnoOut.model_validate(turno)


@router.patch(
    "/turnos/{turno_id}/estado",
    response_model=TurnoOut,
    dependencies=[Depends(require_role("admin", "recepcion", "odontologo"))],
)
def cambiar_estado_turno(
    turno_id: UUID,
    datos: TurnoEstadoUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> TurnoOut:
    servicio = TurnoService(db)
    turno = servicio.cambiar_estado(turno_id, datos.estado)
    return TurnoOut.model_validate(turno)


@router.post(
    "/bloqueos",
    response_model=BloqueoOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "recepcion"))],
)
def crear_bloqueo(
    datos: BloqueoCreate,
    db: Annotated[Session, Depends(get_db)],
) -> BloqueoOut:
    servicio = TurnoService(db)
    bloqueo = servicio.crear_bloqueo(datos)
    return BloqueoOut.model_validate(bloqueo)


@router.delete(
    "/bloqueos/{bloqueo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin", "recepcion"))],
)
def eliminar_bloqueo(
    bloqueo_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    servicio = TurnoService(db)
    servicio.eliminar_bloqueo(bloqueo_id)
    return None


__all__ = ["router"]