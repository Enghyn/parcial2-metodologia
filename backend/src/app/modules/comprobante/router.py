"""Router de comprobante (C-13b)."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.session import get_db
from app.modules.admin.models import Usuario
from app.modules.comprobante.schemas import ComprobanteCreate, ComprobanteOut
from app.modules.comprobante.service import ComprobanteService

router = APIRouter(prefix="/comprobantes", tags=["comprobante"])

_LECTURA = ("admin", "recepcion", "odontologo")
_GESTION = ("admin", "recepcion")


@router.post("", response_model=ComprobanteOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(*_GESTION))])
def crear_comprobante(datos: ComprobanteCreate, db: Annotated[Session, Depends(get_db)], usuario: Annotated[Usuario, Depends(require_role(*_GESTION))]) -> ComprobanteOut:
    return ComprobanteOut.model_validate(ComprobanteService(db).crear(datos, usuario.id))


@router.post("/{comprobante_id}/anular", response_model=ComprobanteOut, dependencies=[Depends(require_role(*_GESTION))])
def anular_comprobante(comprobante_id: UUID, db: Annotated[Session, Depends(get_db)]) -> ComprobanteOut:
    try:
        comp = ComprobanteService(db).anular(comprobante_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no encontrado")
    return ComprobanteOut.model_validate(comp)


@router.get("", response_model=list[ComprobanteOut], dependencies=[Depends(require_role(*_LECTURA))])
def listar_comprobantes(db: Annotated[Session, Depends(get_db)]) -> list[ComprobanteOut]:
    from app.modules.comprobante.models import Comprobante

    return [ComprobanteOut.model_validate(c) for c in db.query(Comprobante).all()]


__all__ = ["router"]