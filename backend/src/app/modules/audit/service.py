"""Helper de registro de auditoría (C-20, D1/D6)."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.admin.models import Usuario
from app.modules.audit.masking import enmascarar
from app.modules.audit.models import Auditoria


def registrar_auditoria(
    db: Session,
    *,
    usuario_id: UUID | None,
    accion: str,
    recurso: str,
    recurso_id: UUID | None = None,
    diff: dict[str, Any] | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> Auditoria:
    """Enmascara y persiste una fila de auditoría en la misma sesión (atómico)."""
    if usuario_id is not None:
        existe = db.scalar(select(Usuario).where(Usuario.id == usuario_id))
        if existe is None:
            usuario_id = None
    auditoria = Auditoria(
        usuario_id=usuario_id,
        accion=accion,
        recurso=recurso,
        recurso_id=recurso_id,
        diff=enmascarar(diff) if diff is not None else None,
        ip=ip,
        user_agent=user_agent,
    )
    db.add(auditoria)
    db.flush()
    return auditoria


__all__ = ["registrar_auditoria"]
