"""Modelo de caja: libro append-only de ingresos y egresos (C-02 core-models-seed)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, ImmutableLedgerMixin

TIPOS_MOVIMIENTO: tuple[str, ...] = ("ingreso", "egreso")
MEDIOS_PAGO: tuple[str, ...] = ("efectivo", "transferencia", "debito", "credito", "otro")


class MovimientoCaja(ImmutableLedgerMixin, Base):
    """Movimiento contable inmutable; las correcciones son contra-asientos (RN-CJ-02)."""

    __tablename__ = "movimientos_caja"
    __table_args__ = (
        CheckConstraint("monto > 0", name="monto"),
        CheckConstraint("tipo IN ('ingreso', 'egreso')", name="tipo"),
        CheckConstraint(
            "medio_pago IN ('efectivo', 'transferencia', 'debito', 'credito', 'otro')",
            name="medio_pago",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    medio_pago: Mapped[str] = mapped_column(String(20), nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    concepto: Mapped[str] = mapped_column(String(255), nullable=False)
    turno_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("turnos.id", name="fk_movimientos_caja_turno_id_turnos"), nullable=True
    )
    usuario_id: Mapped[UUID] = mapped_column(
        ForeignKey("usuarios.id", name="fk_movimientos_caja_usuario_id_usuarios"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
