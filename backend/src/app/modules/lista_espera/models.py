"""Modelo de lista de espera (C-15)."""
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


class ListaEspera(Base, TimestampMixin):
    __tablename__ = "lista_espera"
    __table_args__ = ()

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    paciente_id: Mapped[UUID] = mapped_column(
        ForeignKey("pacientes.id", name="fk_le_paciente"), nullable=False
    )
    profesional_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("profesionales.id", name="fk_le_profesional"), nullable=True
    )
    sillon_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("sillones.id", name="fk_le_sillon"), nullable=True
    )
    fecha_preferida: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'pendiente'"))
    ofrecido_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expira_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)