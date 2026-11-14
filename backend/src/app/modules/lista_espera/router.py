"""Router de lista de espera (C-15)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.session import get_db
from app.modules.lista_espera.schemas import ListaEsperaCreate, ListaEsperaOut
from app.modules.lista_espera.service import ListaEsperaService

router = APIRouter(prefix="/lista-espera", tags=["lista-espera"])

_LECTURA = ("admin", "recepcion", "odontologo")
_GESTION = ("admin", "recepcion")


@router.get("", response_model=list[ListaEsperaOut], dependencies=[Depends(require_role(*_LECTURA))])
def listar(db: Annotated[Session, Depends(get_db)]) -> list[ListaEsperaOut]:
    return [ListaEsperaOut.model_validate(x) for x in ListaEsperaService(db).listar()]


@router.post("", response_model=ListaEsperaOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(*_GESTION))])
def crear(datos: ListaEsperaCreate, db: Annotated[Session, Depends(get_db)]) -> ListaEsperaOut:
    return ListaEsperaOut.model_validate(ListaEsperaService(db).crear(datos))


__all__ = ["router"]