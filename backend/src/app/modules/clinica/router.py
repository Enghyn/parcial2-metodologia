"""Router de ficha clínica (C-07): pacientes y odontograma FDI."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.session import get_db
from app.modules.clinica.schemas import (
    HallazgoIn,
    HallazgoOut,
    OdontogramaOut,
    PacienteCreate,
    PacienteOut,
)
from app.modules.clinica.service import OdontogramaService, PacienteService

router = APIRouter(prefix="/pacientes", tags=["clinica"])

_LECTURA = ("admin", "recepcion", "odontologo")


@router.get(
    "",
    response_model=list[PacienteOut],
    dependencies=[Depends(require_role(*_LECTURA))],
)
def listar_pacientes(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str | None, Query(max_length=100)] = None,
) -> list[PacienteOut]:
    pacientes = PacienteService(db).listar(q=q)
    return [PacienteOut.model_validate(p) for p in pacientes]


@router.post(
    "",
    response_model=PacienteOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "recepcion"))],
)
def crear_paciente(
    datos: PacienteCreate,
    db: Annotated[Session, Depends(get_db)],
) -> PacienteOut:
    return PacienteOut.model_validate(PacienteService(db).crear(datos))


@router.get(
    "/{paciente_id}/odontograma",
    response_model=OdontogramaOut,
    dependencies=[Depends(require_role(*_LECTURA))],
)
def obtener_odontograma(
    paciente_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> OdontogramaOut:
    servicio = OdontogramaService(db)
    odontograma = servicio.obtener_o_crear(paciente_id)
    hallazgos = [HallazgoOut.model_validate(h) for h in servicio.listar_hallazgos(odontograma.id)]
    return OdontogramaOut(
        id=odontograma.id,
        paciente_id=odontograma.paciente_id,
        observaciones_generales=odontograma.observaciones_generales,
        hallazgos=hallazgos,
    )


@router.put(
    "/{paciente_id}/odontograma/piezas/{pieza}",
    response_model=HallazgoOut,
    dependencies=[Depends(require_role("odontologo"))],
)
def upsert_pieza(
    paciente_id: UUID,
    pieza: int,
    datos: HallazgoIn,
    db: Annotated[Session, Depends(get_db)],
) -> HallazgoOut:
    hallazgo = OdontogramaService(db).upsert(paciente_id, pieza, datos)
    return HallazgoOut.model_validate(hallazgo)


__all__ = ["router"]
