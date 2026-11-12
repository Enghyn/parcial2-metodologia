"""Router de presupuestos (C-16)."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.session import get_db
from app.modules.presupuestos.schemas import PresupuestoCreate, PresupuestoOut
from app.modules.presupuestos.service import PresupuestoService

router = APIRouter(prefix="/presupuestos", tags=["presupuestos"])

_LECTURA = ("admin", "recepcion", "odontologo")
_GESTION = ("admin", "recepcion", "odontologo")


@router.get("", response_model=list[PresupuestoOut], dependencies=[Depends(require_role(*_LECTURA))])
def listar(db: Annotated[Session, Depends(get_db)]) -> list[PresupuestoOut]:
    return [PresupuestoOut.model_validate(p) for p in PresupuestoService(db).listar()]


@router.post("", response_model=PresupuestoOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(*_GESTION))])
def crear(datos: PresupuestoCreate, db: Annotated[Session, Depends(get_db)]) -> PresupuestoOut:
    return PresupuestoOut.model_validate(PresupuestoService(db).crear(datos))


@router.post("/aprobar/{token}", response_model=PresupuestoOut)
def aprobar(token: UUID, db: Annotated[Session, Depends(get_db)]) -> PresupuestoOut:
    try:
        p = PresupuestoService(db).aprobar(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no encontrado")
    return PresupuestoOut.model_validate(p)


__all__ = ["router"]