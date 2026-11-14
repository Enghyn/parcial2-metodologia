"""Router de reportes de gestion (C-21): solo lectura, RBAC en backend (R8),
export CSV es-AR (R10). No hay escritura ni migracion."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.core.timezone import ahora
from app.db.session import get_db
from app.modules.admin.models import Usuario
from app.modules.agenda.models import Profesional
from app.modules.reportes.schemas import (
    AusentismoOut,
    FacturacionOut,
    OcupacionOut,
)
from app.modules.reportes.service import ReportesService

router = APIRouter(prefix="/reportes", tags=["reportes"])

_ROLES_LECTURA = ("admin", "recepcion")
_DIAS_DEFAULT = 30


def rango_reporte(
    desde: Annotated[date | None, Query()] = None,
    hasta: Annotated[date | None, Query()] = None,
) -> tuple[date, date]:
    """Aplica default de rango (ultimos 30 dias ART) y valida `desde <= hasta`.

    Levanta 422 cuando el rango queda invertido.
    """
    hoy = ahora().date()
    dia_desde = desde or (hoy - timedelta(days=_DIAS_DEFAULT))
    dia_hasta = hasta or hoy
    if dia_desde > dia_hasta:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="desde no puede ser posterior a hasta",
        )
    return dia_desde, dia_hasta


def usuario_con_filtro_profesional(
    db: Annotated[Session, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(get_current_user)],
) -> tuple[Usuario, UUID | None]:
    """RBAC de reportes (D7).

    - `admin` / `recepcion`: lectura global (`profesional_id = None`).
    - `odontologo`: solo su propia ocupacion (`profesional_id` vinculado al
      usuario); 403 si no hay profesional vinculado.
    """
    if usuario.rol in _ROLES_LECTURA:
        return usuario, None
    if usuario.rol == "odontologo":
        profesional = db.scalar(
            select(Profesional).where(Profesional.usuario_id == usuario.id)
        )
        if profesional is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Rol insuficiente"
            )
        return usuario, profesional.id
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Rol insuficiente"
    )


def _aplicar_filtro_odontologo(
    usuario: Usuario,
    profesional_own: UUID | None,
    profesional_id: UUID | None,
    sillon_id: UUID | None,
) -> tuple[UUID | None, UUID | None]:
    """Devuelve (profesional_id, sillon_id) aplicando la regla del odontologo.

    El odontologo lee solo su propia ocupacion; cualquier otro profesional_id
    genera 403.
    """
    if usuario.rol == "odontologo":
        if profesional_id is not None and profesional_id != profesional_own:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Rol insuficiente"
            )
        return profesional_own, sillon_id
    return profesional_id, sillon_id


@router.get(
    "/ocupacion",
    response_model=OcupacionOut,
    dependencies=[Depends(require_role(*_ROLES_LECTURA, "odontologo"))],
)
def ocupacion(
    rango: Annotated[tuple[date, date], Depends(rango_reporte)],
    db: Annotated[Session, Depends(get_db)],
    auth: Annotated[tuple[Usuario, UUID | None], Depends(usuario_con_filtro_profesional)],
    profesional_id: Annotated[UUID | None, Query()] = None,
    sillon_id: Annotated[UUID | None, Query()] = None,
) -> OcupacionOut:
    desde, hasta = rango
    usuario, profesional_own = auth
    profesional_id, sillon_id = _aplicar_filtro_odontologo(
        usuario, profesional_own, profesional_id, sillon_id
    )
    return ReportesService(db).reporte_ocupacion(desde, hasta, profesional_id, sillon_id)


@router.get(
    "/ocupacion/export.csv",
    dependencies=[Depends(require_role(*_ROLES_LECTURA, "odontologo"))],
)
def export_ocupacion_csv(
    rango: Annotated[tuple[date, date], Depends(rango_reporte)],
    db: Annotated[Session, Depends(get_db)],
    auth: Annotated[tuple[Usuario, UUID | None], Depends(usuario_con_filtro_profesional)],
    profesional_id: Annotated[UUID | None, Query()] = None,
    sillon_id: Annotated[UUID | None, Query()] = None,
) -> Response:
    desde, hasta = rango
    usuario, profesional_own = auth
    profesional_id, sillon_id = _aplicar_filtro_odontologo(
        usuario, profesional_own, profesional_id, sillon_id
    )
    content, filename = ReportesService(db).exportar_ocupacion_csv(
        desde, hasta, profesional_id, sillon_id
    )
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/facturacion",
    response_model=FacturacionOut,
    dependencies=[Depends(require_role(*_ROLES_LECTURA))],
)
def facturacion(
    rango: Annotated[tuple[date, date], Depends(rango_reporte)],
    db: Annotated[Session, Depends(get_db)],
) -> FacturacionOut:
    desde, hasta = rango
    return ReportesService(db).reporte_facturacion(desde, hasta)


@router.get(
    "/facturacion/export.csv",
    dependencies=[Depends(require_role(*_ROLES_LECTURA))],
)
def export_facturacion_csv(
    rango: Annotated[tuple[date, date], Depends(rango_reporte)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    desde, hasta = rango
    content, filename = ReportesService(db).exportar_facturacion_csv(desde, hasta)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/ausentismo",
    response_model=AusentismoOut,
    dependencies=[Depends(require_role(*_ROLES_LECTURA))],
)
def ausentismo(
    rango: Annotated[tuple[date, date], Depends(rango_reporte)],
    db: Annotated[Session, Depends(get_db)],
) -> AusentismoOut:
    desde, hasta = rango
    return ReportesService(db).reporte_ausentismo(desde, hasta)


@router.get(
    "/ausentismo/export.csv",
    dependencies=[Depends(require_role(*_ROLES_LECTURA))],
)
def export_ausentismo_csv(
    rango: Annotated[tuple[date, date], Depends(rango_reporte)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    desde, hasta = rango
    content, filename = ReportesService(db).exportar_ausentismo_csv(desde, hasta)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


__all__ = ["router"]
