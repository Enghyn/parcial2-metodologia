"""Router de ficha clínica (C-07) y ficha clínica avanzada (C-11)."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.session import get_db
from app.modules.admin.models import Usuario
from app.modules.clinica.schemas import (
    ConsentimientoCreate,
    ConsentimientoOut,
    EvolucionCreate,
    EvolucionOut,
    HallazgoIn,
    HallazgoOut,
    HistorialPiezaOut,
    OdontogramaOut,
    PacienteCreate,
    PacienteOut,
)
from app.modules.clinica.service import (
    ConsentimientoService,
    EvolucionService,
    OdontogramaService,
    PacienteService,
)

router = APIRouter(prefix="/pacientes", tags=["clinica"])

_LECTURA = ("admin", "recepcion", "odontologo")
_ODO = ("odontologo",)


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
    hallazgos = [
        HallazgoOut.model_validate(h) for h in servicio.listar_hallazgos(odontograma.id)
    ]
    return OdontogramaOut(
        id=odontograma.id,
        paciente_id=odontograma.paciente_id,
        observaciones_generales=odontograma.observaciones_generales,
        hallazgos=hallazgos,
    )


@router.put(
    "/{paciente_id}/odontograma/piezas/{pieza}",
    response_model=HallazgoOut,
)
def upsert_pieza(
    paciente_id: UUID,
    pieza: int,
    datos: HallazgoIn,
    db: Annotated[Session, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(require_role("odontologo"))],
) -> HallazgoOut:
    hallazgo = OdontogramaService(db).upsert(
        paciente_id=paciente_id, pieza=pieza, datos=datos, usuario=usuario
    )
    return HallazgoOut.model_validate(hallazgo)


# ── C-11: Evolución clínica ──────────────────────────────────────────────

@router.post(
    "/{paciente_id}/evoluciones",
    response_model=EvolucionOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(*_ODO))],
)
def crear_evolucion(
    paciente_id: UUID,
    datos: EvolucionCreate,
    db: Annotated[Session, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(require_role(*_ODO))],
) -> EvolucionOut:
    evo = EvolucionService(db).crear(
        paciente_id=paciente_id,
        texto=datos.texto,
        autor_usuario_id=usuario.id,
    )
    return EvolucionOut.model_validate(evo)


@router.get(
    "/{paciente_id}/evoluciones",
    response_model=list[EvolucionOut],
    dependencies=[Depends(require_role(*_LECTURA))],
)
def listar_evoluciones(
    paciente_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> list[EvolucionOut]:
    return [
        EvolucionOut.model_validate(e)
        for e in EvolucionService(db).listar(paciente_id=paciente_id)
    ]


# ── C-11: Consentimiento informado ───────────────────────────────────────

@router.post(
    "/{paciente_id}/consentimientos",
    response_model=ConsentimientoOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(*_ODO))],
)
def crear_consentimiento(
    paciente_id: UUID,
    datos: ConsentimientoCreate,
    db: Annotated[Session, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(require_role(*_ODO))],
) -> ConsentimientoOut:
    cons = ConsentimientoService(db).crear(
        paciente_id=paciente_id,
        version=datos.version,
        autor_usuario_id=usuario.id,
    )
    return ConsentimientoOut.model_validate(cons)


@router.get(
    "/{paciente_id}/consentimientos",
    response_model=list[ConsentimientoOut],
    dependencies=[Depends(require_role(*_LECTURA))],
)
def listar_consentimientos(
    paciente_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> list[ConsentimientoOut]:
    return [
        ConsentimientoOut.model_validate(c)
        for c in ConsentimientoService(db).listar(paciente_id=paciente_id)
    ]


# ── C-11: Historial por pieza ──────────────────────────────────────────────

@router.get(
    "/{paciente_id}/odontograma/piezas/{pieza}/historial",
    response_model=list[HistorialPiezaOut],
    dependencies=[Depends(require_role(*_LECTURA))],
)
def listar_historial_pieza(
    paciente_id: UUID,
    pieza: int,
    db: Annotated[Session, Depends(get_db)],
) -> list[HistorialPiezaOut]:
    servicio = OdontogramaService(db)
    # Validar pieza FDI
    if not (11 <= pieza <= 48 and 1 <= pieza % 10 <= 8):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Pieza FDI inválida: usá 11–18, 21–28, 31–38 o 41–48",
        )
    # Validar paciente vigente
    servicio._paciente_vigente(paciente_id)
    odontograma = servicio.obtener_o_crear(paciente_id)
    historial = servicio.listar_historial(odontograma.id, pieza)
    return [
        HistorialPiezaOut.model_validate(h) for h in historial
    ]


__all__ = ["router"]
