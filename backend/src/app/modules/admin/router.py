"""Router admin (C-19)."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.session import get_db
from app.modules.admin.schemas import (
    ProfesionalCreate,
    ProfesionalOut,
    SillonCreate,
    SillonOut,
    UsuarioCreate,
    UsuarioOut,
)
from app.modules.admin.service import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])

_ADMIN = ("admin",)


@router.get("/usuarios", response_model=list[UsuarioOut], dependencies=[Depends(require_role(*_ADMIN))])
def listar_usuarios(db: Annotated[Session, Depends(get_db)]) -> list[UsuarioOut]:
    return [UsuarioOut.model_validate(u) for u in AdminService(db).listar_usuarios()]


@router.post("/usuarios", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(*_ADMIN))])
def crear_usuario(datos: UsuarioCreate, db: Annotated[Session, Depends(get_db)]) -> UsuarioOut:
    return UsuarioOut.model_validate(AdminService(db).crear_usuario(datos))


@router.delete("/usuarios/{usuario_id}", response_model=UsuarioOut, dependencies=[Depends(require_role(*_ADMIN))])
def desactivar_usuario(usuario_id: UUID, db: Annotated[Session, Depends(get_db)]) -> UsuarioOut:
    try:
        u = AdminService(db).desactivar_usuario(usuario_id)
    except ValueError as e:
        if str(e) == "ultimo_admin":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ultimo admin activo")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no encontrado")
    return UsuarioOut.model_validate(u)


@router.get("/sillones", response_model=list[SillonOut], dependencies=[Depends(require_role(*_ADMIN))])
def listar_sillones(db: Annotated[Session, Depends(get_db)]) -> list[SillonOut]:
    return [SillonOut.model_validate(s) for s in AdminService(db).listar_sillones()]


@router.post("/sillones", response_model=SillonOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(*_ADMIN))])
def crear_sillon(datos: SillonCreate, db: Annotated[Session, Depends(get_db)]) -> SillonOut:
    return SillonOut.model_validate(AdminService(db).crear_sillon(datos))


@router.delete("/sillones/{sillon_id}", response_model=SillonOut, dependencies=[Depends(require_role(*_ADMIN))])
def baja_sillon(sillon_id: UUID, db: Annotated[Session, Depends(get_db)]) -> SillonOut:
    try:
        s = AdminService(db).baja_sillon(sillon_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no encontrado")
    return SillonOut.model_validate(s)


@router.get("/profesionales", response_model=list[ProfesionalOut], dependencies=[Depends(require_role(*_ADMIN))])
def listar_profesionales(db: Annotated[Session, Depends(get_db)]) -> list[ProfesionalOut]:
    return [ProfesionalOut.model_validate(p) for p in AdminService(db).listar_profesionales()]


@router.post("/profesionales", response_model=ProfesionalOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(*_ADMIN))])
def crear_profesional(datos: ProfesionalCreate, db: Annotated[Session, Depends(get_db)]) -> ProfesionalOut:
    return ProfesionalOut.model_validate(AdminService(db).crear_profesional(datos))


@router.delete("/profesionales/{profesional_id}", response_model=ProfesionalOut, dependencies=[Depends(require_role(*_ADMIN))])
def baja_profesional(profesional_id: UUID, db: Annotated[Session, Depends(get_db)]) -> ProfesionalOut:
    try:
        p = AdminService(db).baja_profesional(profesional_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no encontrado")
    return ProfesionalOut.model_validate(p)


__all__ = ["router"]