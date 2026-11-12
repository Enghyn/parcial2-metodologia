"""Modelos de pagos simulados (C-17)."""
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


class Pago(Base, TimestampMixin):
    __tablename__ = "pagos"
    __table_args__ = ()

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    presupuesto_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("presupuestos.id", name="fk_pago_presupuesto"), nullable=True
    )
    monto: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'pendiente'"))
    movimiento_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("movimientos_caja.id", name="fk_pago_movimiento"), nullable=True
    )
    confirmado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IntentoPago(Base, TimestampMixin):
    __tablename__ = "intentos_pago"
    __table_args__ = ()

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    pago_id: Mapped[UUID] = mapped_column(
        ForeignKey("pagos.id", name="fk_intento_pago"), nullable=False
    )
    resultado: Mapped[str] = mapped_column(String(20), nullable=False)
    procesado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())