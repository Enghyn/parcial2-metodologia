"""Router de nomenclador (C-13a)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.session import get_db
from app.modules.nomenclador.schemas import (
    ConvenioPracticaCreate,
    ConvenioPracticaOut,
    PracticaCreate,
    PracticaOut,
)
from app.modules.nomenclador.service import NomencladorService

router = APIRouter(prefix="/nomenclador", tags=["nomenclador"])

_LECTURA = ("admin", "recepcion", "odontologo")
_GESTION = ("admin",)


@router.get("/practicas", response_model=list[PracticaOut], dependencies=[Depends(require_role(*_LECTURA))])
def listar_practicas(db: Annotated[Session, Depends(get_db)]) -> list[PracticaOut]:
    return [PracticaOut.model_validate(p) for p in NomencladorService(db).listar_practicas()]


@router.post("/practicas", response_model=PracticaOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(*_GESTION))])
def crear_practica(datos: PracticaCreate, db: Annotated[Session, Depends(get_db)]) -> PracticaOut:
    return PracticaOut.model_validate(NomencladorService(db).crear_practica(datos))


@router.post("/convenio-practicas", response_model=ConvenioPracticaOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(*_GESTION))])
def crear_convenio_practica(datos: ConvenioPracticaCreate, db: Annotated[Session, Depends(get_db)]) -> ConvenioPracticaOut:
    return ConvenioPracticaOut.model_validate(NomencladorService(db).crear_convenio_practica(datos))


__all__ = ["router"]