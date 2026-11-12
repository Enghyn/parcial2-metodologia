"""Modelo de notificación (C-14)."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Notificacion(Base, TimestampMixin):
    __tablename__ = "notificaciones"
    __table_args__ = ()

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    turno_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("turnos.id", name="fk_notif_turno"), nullable=True
    )
    plantilla: Mapped[str] = mapped_column(String(50), nullable=False)
    destinatario: Mapped[str] = mapped_column(String(100), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'pendiente'"))
    enviado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)