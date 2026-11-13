"""Router de auditoría (C-20): visor paginado y export CSV (solo admin)."""
from __future__ import annotations

import csv
import io
import json
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.core.timezone import fin_dia, inicio_dia
from app.db.session import get_db
from app.modules.admin.models import Usuario
from app.modules.audit.masking import enmascarar
from app.modules.audit.models import Auditoria
from app.modules.audit.schemas import AuditoriaOut

router = APIRouter(prefix="/auditoria", tags=["auditoria"])

_ROLES_ADMIN = ("admin",)
_TOPE_EXPORT = 10000


def _filtros_query(
    db: Session,
    *,
    fecha_desde: date | None,
    fecha_hasta: date | None,
    recurso: str | None,
    accion: str | None,
    usuario_id: UUID | None,
) -> list[Auditoria]:
    stmt = select(Auditoria)
    if fecha_desde is not None:
        stmt = stmt.where(Auditoria.fecha >= inicio_dia(fecha_desde))
    if fecha_hasta is not None:
        stmt = stmt.where(Auditoria.fecha < fin_dia(fecha_hasta))
    if recurso is not None:
        stmt = stmt.where(Auditoria.recurso == recurso)
    if accion is not None:
        stmt = stmt.where(Auditoria.accion == accion)
    if usuario_id is not None:
        stmt = stmt.where(Auditoria.usuario_id == usuario_id)
    stmt = stmt.order_by(Auditoria.fecha.desc())
    return list(db.scalars(stmt))


@router.get("", response_model=list[AuditoriaOut])
def listar_auditoria(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[Usuario, Depends(require_role(*_ROLES_ADMIN))],
    fecha_desde: Annotated[date | None, Query()] = None,
    fecha_hasta: Annotated[date | None, Query()] = None,
    recurso: Annotated[str | None, Query()] = None,
    accion: Annotated[str | None, Query()] = None,
    usuario_id: Annotated[UUID | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=50)] = 50,
) -> list[AuditoriaOut]:
    filas = _filtros_query(
        db,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        recurso=recurso,
        accion=accion,
        usuario_id=usuario_id,
    )
    inicio = (page - 1) * size
    pagina = filas[inicio : inicio + size]
    return [AuditoriaOut.model_validate(f) for f in pagina]


@router.get("/export")
def exportar_auditoria(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[Usuario, Depends(require_role(*_ROLES_ADMIN))],
    fecha_desde: Annotated[date | None, Query()] = None,
    fecha_hasta: Annotated[date | None, Query()] = None,
    recurso: Annotated[str | None, Query()] = None,
    accion: Annotated[str | None, Query()] = None,
    usuario_id: Annotated[UUID | None, Query()] = None,
) -> Response:
    filas = _filtros_query(
        db,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        recurso=recurso,
        accion=accion,
        usuario_id=usuario_id,
    )
    if len(filas) > _TOPE_EXPORT:
        return Response(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content="Export supera el tope de filas",
        )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["id", "fecha", "usuario_id", "accion", "recurso", "recurso_id", "diff", "ip", "user_agent"]
    )
    for f in filas:
        diff_enmascarado = enmascarar(f.diff) if f.diff is not None else None
        writer.writerow(
            [
                str(f.id),
                f.fecha.isoformat() if f.fecha is not None else "",
                str(f.usuario_id) if f.usuario_id is not None else "",
                f.accion,
                f.recurso,
                str(f.recurso_id) if f.recurso_id is not None else "",
                ("" if diff_enmascarado is None else json.dumps(diff_enmascarado, ensure_ascii=False)),
                f.ip or "",
                f.user_agent or "",
            ]
        )
    content = buffer.getvalue()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="auditoria.csv"'},
    )


__all__ = ["router"]
