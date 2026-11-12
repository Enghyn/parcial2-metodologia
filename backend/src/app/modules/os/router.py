"""Router de OS, convenios y afiliación (C-13a)."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.session import get_db
from app.modules.os.schemas import (
    AfiliacionCreate,
    AfiliacionOut,
    ConvenioCreate,
    ConvenioOut,
    ObraSocialCreate,
    ObraSocialOut,
)
from app.modules.os.service import AfiliacionService, ConvenioService, ObraSocialService

router = APIRouter(prefix="/os", tags=["os"])

_LECTURA = ("admin", "recepcion", "odontologo")
_GESTION = ("admin",)


@router.get("/obras-sociales", response_model=list[ObraSocialOut], dependencies=[Depends(require_role(*_LECTURA))])
def listar_obras_sociales(db: Annotated[Session, Depends(get_db)]) -> list[ObraSocialOut]:
    return [ObraSocialOut.model_validate(o) for o in ObraSocialService(db).listar()]


@router.post("/obras-sociales", response_model=ObraSocialOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(*_GESTION))])
def crear_obra_social(datos: ObraSocialCreate, db: Annotated[Session, Depends(get_db)]) -> ObraSocialOut:
    try:
        os_ = ObraSocialService(db).crear(datos)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="nombre duplicado")
    return ObraSocialOut.model_validate(os_)


@router.get("/convenios", response_model=list[ConvenioOut], dependencies=[Depends(require_role(*_LECTURA))])
def listar_convenios(obra_social_id: UUID | None = None, db: Annotated[Session, Depends(get_db)] = None) -> list[ConvenioOut]:  # type: ignore[assignment]
    return [ConvenioOut.model_validate(c) for c in ConvenioService(db).listar(obra_social_id)]


@router.post("/convenios", response_model=ConvenioOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(*_GESTION))])
def crear_convenio(datos: ConvenioCreate, db: Annotated[Session, Depends(get_db)]) -> ConvenioOut:
    return ConvenioOut.model_validate(ConvenioService(db).crear(datos))


@router.post("/afiliaciones", response_model=AfiliacionOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(*_GESTION))])
def crear_afiliacion(datos: AfiliacionCreate, db: Annotated[Session, Depends(get_db)]) -> AfiliacionOut:
    return AfiliacionOut.model_validate(AfiliacionService(db).crear(datos))


__all__ = ["router"]