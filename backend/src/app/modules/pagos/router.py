"""Router de pagos (C-17)."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.session import get_db
from app.modules.admin.models import Usuario
from app.modules.pagos.schemas import PagoCreate, PagoOut
from app.modules.pagos.service import PagoService

router = APIRouter(prefix="/pagos", tags=["pagos"])

_LECTURA = ("admin", "recepcion", "odontologo")
_GESTION = ("admin", "recepcion")


@router.get("", response_model=list[PagoOut], dependencies=[Depends(require_role(*_LECTURA))])
def listar(db: Annotated[Session, Depends(get_db)]) -> list[PagoOut]:
    return [PagoOut.model_validate(p) for p in PagoService(db).listar()]


@router.post("", response_model=PagoOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(*_GESTION))])
def crear(datos: PagoCreate, db: Annotated[Session, Depends(get_db)]) -> PagoOut:
    return PagoOut.model_validate(PagoService(db).crear(datos))


@router.post("/{pago_id}/confirmar", response_model=PagoOut)
def confirmar(
    pago_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(require_role(*_GESTION))],
) -> PagoOut:
    try:
        p = PagoService(db).confirmar(pago_id, usuario.id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no encontrado")
    return PagoOut.model_validate(p)


__all__ = ["router"]