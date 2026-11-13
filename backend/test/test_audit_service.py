"""Tests de servicio de auditoría (C-20): persistencia y atomicidad."""
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_session_factory
from app.modules.admin.models import Usuario
from app.modules.agenda.models import Sillon
from app.modules.audit.models import Auditoria
from app.modules.audit.service import registrar_auditoria

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("db_disponible")]


def _session() -> Session:
    return get_session_factory()()


def test_registrar_auditoria_persiste_y_enmascara() -> None:
    session = _session()
    try:
        usuario = session.scalar(select(Usuario).where(Usuario.rol == "admin"))
        assert usuario is not None
        from uuid import uuid4

        recurso_id = uuid4()
        auditoria = registrar_auditoria(
            session,
            usuario_id=usuario.id,
            accion="crear",
            recurso="turno",
            recurso_id=recurso_id,
            diff={"observacion": "secreto", "prestacion": "Consulta"},
        )
        session.commit()
        row = session.scalar(select(Auditoria).where(Auditoria.id == auditoria.id))
        assert row is not None
        assert row.diff["observacion"] == "[REDACTED]"
        assert row.diff["prestacion"] == "Consulta"
        assert row.recurso_id == recurso_id
    finally:
        session.close()


def test_fallo_auditoria_revierte_escritura() -> None:
    session = _session()
    try:
        sillon = Sillon(nombre="AuditTest", activo=True)
        session.add(sillon)
        session.flush()
        sillon_id = sillon.id
        with pytest.raises(IntegrityError):
            registrar_auditoria(
                session,
                usuario_id=None,
                accion="crear",
                recurso="recurso_invalido",
                recurso_id=sillon_id,
                diff=None,
            )
            session.commit()
        session.rollback()
        encontrado = session.scalar(select(Sillon).where(Sillon.id == sillon_id))
        assert encontrado is None
    finally:
        session.close()
