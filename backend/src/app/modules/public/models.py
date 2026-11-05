"""Modelo de pre-reserva (retención temporal del hueco, C-10, D1)."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class PreReserva(TimestampMixin, Base):
    """Retención efímera de un hueco (no es un turno, D1/D3).

    No hereda `SoftDeleteMixin`: el ciclo se cubre con `estado`
    (vigente/consumida/expirada/cancelada) y nunca se borra físicamente.
    """

    __tablename__ = "pre_reservas"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('vigente', 'consumida', 'expirada', 'cancelada')",
            name="ck_pre_reservas_estado",
        ),
        CheckConstraint("fin > inicio", name="ck_pre_reservas_rango"),
        CheckConstraint(
            "fin = inicio + (duracion_min * interval '1 minute')",
            name="ck_pre_reservas_fin_coherente",
        ),
        UniqueConstraint("token", name="uq_pre_reservas_token"),
        UniqueConstraint("turno_id", name="uq_pre_reservas_turno_id"),
        Index("ix_pre_reservas_sillon_inicio_fin", "sillon_id", "inicio", "fin"),
        Index("ix_pre_reservas_profesional_inicio_fin", "profesional_id", "inicio", "fin"),
        Index("ix_pre_reservas_expira_en", "expira_en"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    token: Mapped[UUID] = mapped_column(
        Uuid, nullable=False, default=uuid4, server_default=text("gen_random_uuid()")
    )
    sillon_id: Mapped[UUID] = mapped_column(
        ForeignKey("sillones.id", name="fk_pre_reservas_sillon_id_sillones"), nullable=False
    )
    profesional_id: Mapped[UUID] = mapped_column(
        ForeignKey("profesionales.id", name="fk_pre_reservas_profesional_id_profesionales"),
        nullable=False,
    )
    prestacion: Mapped[str] = mapped_column(String(150), nullable=False)
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duracion_min: Mapped[int] = mapped_column(Integer, nullable=False)
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="vigente", server_default=text("'vigente'")
    )
    turno_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("turnos.id", name="fk_pre_reservas_turno_id_turnos"), nullable=True
    )

