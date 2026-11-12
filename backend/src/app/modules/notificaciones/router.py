"""Router de notificaciones (C-14)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.session import get_db
from app.modules.notificaciones.schemas import NotificacionCreate, NotificacionOut
from app.modules.notificaciones.service import NotificacionService

router = APIRouter(prefix="/notificaciones", tags=["notificaciones"])

_LECTURA = ("admin", "recepcion", "odontologo")
_GESTION = ("admin", "recepcion")


@router.get("", response_model=list[NotificacionOut], dependencies=[Depends(require_role(*_LECTURA))])
def listar(db: Annotated[Session, Depends(get_db)]) -> list[NotificacionOut]:
    return [NotificacionOut.model_validate(n) for n in NotificacionService(db).listar()]


@router.post("", response_model=NotificacionOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(*_GESTION))])
def crear(datos: NotificacionCreate, db: Annotated[Session, Depends(get_db)]) -> NotificacionOut:
    return NotificacionOut.model_validate(NotificacionService(db).crear(datos))


__all__ = ["router"]