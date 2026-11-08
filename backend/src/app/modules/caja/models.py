"""Modelo de caja: libro append-only de ingresos y egresos (C-02 core-models-seed)."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
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


class CierreCaja(Base):
    """Cierre diario de caja por día calendario ART.

    Una fila por día (fecha_dia UNIQUE). Estado `cerrado` bloquea nuevos
    movimientos de ese día (bloqueo de período, RN-CJ-01 / D1).
    """

    __tablename__ = "cierres_caja"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('pendiente', 'cerrado', 'reabierto')",
            name="estado",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    fecha_dia: Mapped[date] = mapped_column(
        Date, nullable=False, unique=True
    )
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_ingresos: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_egresos: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    aprobado_por: Mapped[UUID | None] = mapped_column(
        ForeignKey("usuarios.id", name="fk_cierres_aprobado_por_usuarios"),
        nullable=True,
    )
    aprobado_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class CuentaCorrientePaciente(Base):
    """Cuenta corriente de un paciente: saldo derivado de movimientos vinculados a sus turnos.

    Es una tabla derivada/materializada: el saldo se recalcula desde
    `movimientos_caja` (no es fuente de verdad autónoma, D2).
    La PK es `paciente_id` (única), no hay ID auto-generado.
    """

    __tablename__ = "cuentas_corrientes_paciente"

    paciente_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "pacientes.id", name="fk_cuenta_corriente_paciente_id_pacientes"
        ),
        nullable=False,
        primary_key=True,
    )
    saldo: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, server_default=text("0.00")
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class AjusteCaja(ImmutableLedgerMixin, Base):
    """Ajuste auditado: vincula el movimiento corregido con su contra-asiento.

    Nunca se toca el movimiento original (RN-CJ-02, R3, R13). Append-only:
    triggers bloquean UPDATE/DELETE (D3).
    """

    __tablename__ = "ajustes_caja"
    __table_args__ = (
        CheckConstraint(
            "length(btrim(motivo)) > 0", name="motivo_no_vacio"
        ),
        CheckConstraint(
            "movimiento_corregido_id <> movimiento_ajuste_id",
            name="movimientos_distintos",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    movimiento_corregido_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "movimientos_caja.id",
            name="fk_ajustes_movimiento_corregido_id_movimientos_caja",
        ),
        nullable=False,
    )
    movimiento_ajuste_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "movimientos_caja.id",
            name="fk_ajustes_movimiento_ajuste_id_movimientos_caja",
        ),
        nullable=False,
    )
    motivo: Mapped[str] = mapped_column(String(255), nullable=False)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    usuario_aprobador_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "usuarios.id", name="fk_ajustes_usuario_aprobador_id_usuarios"
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
