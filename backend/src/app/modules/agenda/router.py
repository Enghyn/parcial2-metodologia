"""Router agenda (C-04): endpoints de turnos y bloqueos con RBAC (D7/D8)."""
from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.session import get_db
from app.modules.admin.models import Usuario
from app.modules.agenda.schemas import (
    BloqueoCreate,
    BloqueoOut,
    FiltroTurnos,
    ProfesionalOut,
    ReprogramarTurno,
    SillonOut,
    SobreturnoCreate,
    TurnoCreate,
    TurnoEstadoUpdate,
    TurnoOut,
)
from app.modules.agenda.service import TurnoService

router = APIRouter(tags=["agenda"])


def _servicio(db: Session) -> TurnoService:
    return TurnoService(db)


def _mensaje_validacion(exc: ValidationError) -> str:
    """Primer mensaje de `FiltroTurnos`, sin el prefijo de pydantic (R10)."""
    errores = exc.errors()
    if not errores:
        return "Filtros de turnos inválidos"
    mensaje = str(errores[0].get("msg", ""))
    return mensaje.removeprefix("Value error, ") or "Filtros de turnos inválidos"


def filtro_turnos(
    fecha: Annotated[
        date | None,
        Query(description="Día ART (YYYY-MM-DD). Excluyente con desde/hasta."),
    ] = None,
    desde: Annotated[
        date | None, Query(description="Primer día ART del rango, inclusive.")
    ] = None,
    hasta: Annotated[
        date | None,
        Query(description="Último día ART del rango, inclusive (máximo 31 días)."),
    ] = None,
    profesional_id: Annotated[
        UUID | None, Query(description="Filtra por profesional.")
    ] = None,
    sillon_id: Annotated[UUID | None, Query(description="Filtra por sillón.")] = None,
) -> FiltroTurnos:
    """Valida los filtros de `GET /turnos` con `FiltroTurnos` (C-09b, D2).

    Los parámetros se declaran explícitos para que FastAPI los documente y siga
    ignorando los query params desconocidos (compatibilidad con clientes
    actuales); el modelo aporta las reglas del rango y `extra="forbid"` (R1).
    """
    try:
        return FiltroTurnos(
            fecha=fecha,
            desde=desde,
            hasta=hasta,
            profesional_id=profesional_id,
            sillon_id=sillon_id,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=_mensaje_validacion(exc),
        ) from exc


@router.get(
    "/turnos",
    response_model=list[TurnoOut],
    dependencies=[Depends(require_role("admin", "recepcion", "odontologo"))],
)
def listar_turnos(
    db: Annotated[Session, Depends(get_db)],
    filtro: Annotated[FiltroTurnos, Depends(filtro_turnos)],
) -> list[TurnoOut]:
    """Lista turnos vivos del día `fecha` o del rango inclusivo `desde`/`hasta`.

    Los días se interpretan en ART (D1) y el orden es determinista:
    `inicio`, `sillon_id`, `id` (D3). Los `cancelado` se incluyen (D5).
    """
    servicio = TurnoService(db)
    turnos = servicio.listar(
        fecha=filtro.fecha,
        desde=filtro.desde,
        hasta=filtro.hasta,
        profesional_id=filtro.profesional_id,
        sillon_id=filtro.sillon_id,
    )
    return [TurnoOut.model_validate(t) for t in turnos]


@router.get(
    "/sillones",
    response_model=list[SillonOut],
    dependencies=[Depends(require_role("admin", "recepcion", "odontologo"))],
)
def listar_sillones(db: Annotated[Session, Depends(get_db)]) -> list[SillonOut]:
    """Sillones activos del consultorio: una fila por sillón en la grilla (C-09b).

    Sin este catálogo la SPA cae a IDs ficticios y no puede asociar un turno a
    su sillón (defecto detectado al aplicar la vista semanal).
    """
    return [SillonOut.model_validate(s) for s in TurnoService(db).listar_sillones()]


@router.get(
    "/profesionales",
    response_model=list[ProfesionalOut],
    dependencies=[Depends(require_role("admin", "recepcion", "odontologo"))],
)
def listar_profesionales(db: Annotated[Session, Depends(get_db)]) -> list[ProfesionalOut]:
    """Profesionales activos: alimenta el filtro y el nombre de cada chip (C-09b)."""
    return [
        ProfesionalOut.model_validate(p)
        for p in TurnoService(db).listar_profesionales()
    ]


@router.post(
    "/turnos",
    response_model=TurnoOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "recepcion"))],
)
def crear_turno(
    datos: TurnoCreate,
    db: Annotated[Session, Depends(get_db)],
) -> TurnoOut:
    servicio = TurnoService(db)
    turno = servicio.crear(datos)
    return TurnoOut.model_validate(turno)


@router.post(
    "/turnos/sobreturno",
    response_model=TurnoOut,
    status_code=status.HTTP_201_CREATED,
)
def crear_sobreturno(
    datos: SobreturnoCreate,
    db: Annotated[Session, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(require_role("admin", "recepcion"))],
) -> TurnoOut:
    turno = TurnoService(db).crear_sobreturno(datos, usuario.id)
    return TurnoOut.model_validate(turno)


@router.patch(
    "/turnos/{turno_id}/reprogramar",
    response_model=TurnoOut,
    dependencies=[Depends(require_role("admin", "recepcion"))],
)
def reprogramar_turno(
    turno_id: UUID,
    datos: ReprogramarTurno,
    db: Annotated[Session, Depends(get_db)],
) -> TurnoOut:
    turno = TurnoService(db).reprogramar(turno_id, datos)
    return TurnoOut.model_validate(turno)


@router.patch(
    "/turnos/{turno_id}/estado",
    response_model=TurnoOut,
    dependencies=[Depends(require_role("admin", "recepcion", "odontologo"))],
)
def cambiar_estado_turno(
    turno_id: UUID,
    datos: TurnoEstadoUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> TurnoOut:
    servicio = TurnoService(db)
    turno = servicio.cambiar_estado(turno_id, datos.estado)
    return TurnoOut.model_validate(turno)


@router.post(
    "/bloqueos",
    response_model=BloqueoOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "recepcion"))],
)
def crear_bloqueo(
    datos: BloqueoCreate,
    db: Annotated[Session, Depends(get_db)],
) -> BloqueoOut:
    servicio = TurnoService(db)
    bloqueo = servicio.crear_bloqueo(datos)
    return BloqueoOut.model_validate(bloqueo)


@router.delete(
    "/bloqueos/{bloqueo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin", "recepcion"))],
)
def eliminar_bloqueo(
    bloqueo_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    servicio = TurnoService(db)
    servicio.eliminar_bloqueo(bloqueo_id)


__all__ = ["router"]