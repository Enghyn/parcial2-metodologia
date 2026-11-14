"""Modelo de comprobante manual (C-13b)."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Comprobante(Base, TimestampMixin):
    __tablename__ = "comprobantes"
    __table_args__ = (  # type: ignore[assignment]
    )

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    numero: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    movimiento_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("movimientos_caja.id", name="fk_comp_movimiento"), nullable=True
    )
    presupuesto_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'pendiente'"))
    emitido_por: Mapped[UUID | None] = mapped_column(
        ForeignKey("usuarios.id", name="fk_comp_emitido_por"), nullable=True
    )
    emitido_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    anulado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)