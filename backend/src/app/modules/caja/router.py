"""Router de caja (C-08): movimientos append-only y resumen diario."""
from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.session import get_db
from app.modules.admin.models import Usuario
from app.modules.caja.schemas import (
    MovimientoCreate,
    MovimientoOut,
    ResumenDiarioOut,
)
from app.modules.caja.service import CajaService

router = APIRouter(prefix="/caja", tags=["caja"])

_ROLES_CAJA = ("admin", "recepcion")


@router.post(
    "/movimientos",
    response_model=MovimientoOut,
    status_code=status.HTTP_201_CREATED,
)
def crear_movimiento(
    datos: MovimientoCreate,
    db: Annotated[Session, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(require_role(*_ROLES_CAJA))],
) -> MovimientoOut:
    movimiento = CajaService(db).registrar(datos, usuario.id)
    return MovimientoOut.model_validate(movimiento)


@router.get(
    "/movimientos",
    response_model=list[MovimientoOut],
    dependencies=[Depends(require_role(*_ROLES_CAJA))],
)
def listar_movimientos(
    db: Annotated[Session, Depends(get_db)],
    fecha: Annotated[date | None, Query()] = None,
) -> list[MovimientoOut]:
    return [MovimientoOut.model_validate(m) for m in CajaService(db).listar(fecha)]


@router.get(
    "/resumen-diario",
    response_model=ResumenDiarioOut,
    dependencies=[Depends(require_role(*_ROLES_CAJA))],
)
def resumen_diario(
    db: Annotated[Session, Depends(get_db)],
    fecha: Annotated[date | None, Query()] = None,
) -> ResumenDiarioOut:
    return CajaService(db).resumen(fecha)


__all__ = ["router"]
