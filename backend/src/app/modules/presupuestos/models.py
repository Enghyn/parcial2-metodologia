"""Modelos de presupuestos (C-16)."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Presupuesto(Base, TimestampMixin):
    __tablename__ = "presupuestos"
    __table_args__ = ()

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    paciente_id: Mapped[UUID] = mapped_column(
        ForeignKey("pacientes.id", name="fk_pres_paciente"), nullable=False
    )
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'borrador'"))
    total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, server_default=text("0.00"))
    token_publico: Mapped[UUID] = mapped_column(
        Uuid, nullable=False, default=uuid4, server_default=text("gen_random_uuid()")
    )
    aprobado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ItemPresupuesto(Base, TimestampMixin):
    __tablename__ = "items_presupuesto"
    __table_args__ = ()

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    presupuesto_id: Mapped[UUID] = mapped_column(
        ForeignKey("presupuestos.id", name="fk_item_presupuesto"), nullable=False
    )
    descripcion: Mapped[str] = mapped_column(String(255), nullable=False)
    cantidad: Mapped[int] = mapped_column(nullable=False, server_default=text("1"))
    arancel: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    copago: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, server_default=text("0.00"))