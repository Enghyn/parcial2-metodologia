"""Modelo SQLAlchemy de `auditorias` (C-20)."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

_ACCIONES = (
    "crear",
    "actualizar",
    "eliminar",
    "cancelar",
    "reprogramar",
    "cerrar",
    "reabrir",
    "ajustar",
    "aprobar",
    "cambiar_estado",
    "registrar",
)

_RECURSOS = (
    "turno",
    "bloqueo",
    "movimiento_caja",
    "movimiento",
    "caja",
    "cierre_caja",
    "cierre",
    "ajuste_caja",
    "ajuste",
    "presupuesto",
    "hallazgo_pieza",
    "hallazgo",
    "odontograma",
    "paciente",
)


class Auditoria(Base):
    """Fila de auditoría: quién hizo qué y cuándo (append-only de trazabilidad)."""

    __tablename__ = "auditorias"
    __table_args__ = (
        CheckConstraint(
            "accion IN (" + ", ".join(f"'{v}'" for v in _ACCIONES) + ")",
            name="accion",
        ),
        CheckConstraint(
            "recurso IN (" + ", ".join(f"'{v}'" for v in _RECURSOS) + ")",
            name="recurso",
        ),
        Index("ix_auditorias_fecha", "fecha"),
        Index("ix_auditorias_recurso_recurso_id", "recurso", "recurso_id"),
        Index("ix_auditorias_usuario_id", "usuario_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    usuario_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("usuarios.id", name="fk_auditorias_usuario_id_usuarios", ondelete="SET NULL"),
        nullable=True,
    )
    accion: Mapped[str] = mapped_column(String(40), nullable=False)
    recurso: Mapped[str] = mapped_column(String(60), nullable=False)
    recurso_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    diff: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)


__all__ = ["Auditoria"]
