"""Modelos de agenda: sillones, profesionales, turnos y bloqueos (C-02)."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin

ESTADOS_TURNO: tuple[str, ...] = (
    "reservado",
    "confirmado",
    "presente",
    "atendido",
    "cancelado",
    "ausente",
)


class Sillon(SoftDeleteMixin, TimestampMixin, Base):
    """Capacidad física del consultorio (2 a 3 sillones, R2)."""

    __tablename__ = "sillones"

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )


class Profesional(SoftDeleteMixin, TimestampMixin, Base):
    """Odontólogo que atiende en el consultorio; usuario interno opcional."""

    __tablename__ = "profesionales"
    __table_args__ = (
        UniqueConstraint("usuario_id", name="usuario_id"),
        UniqueConstraint("matricula", name="matricula"),
        CheckConstraint("duracion_default_min > 0", name="duracion"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    usuario_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("usuarios.id", name="fk_profesionales_usuario_id_usuarios"), nullable=True
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    matricula: Mapped[str] = mapped_column(String(50), nullable=False)
    especialidad: Mapped[str] = mapped_column(String(100), nullable=False)
    duracion_default_min: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30, server_default=text("30")
    )
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )


class Turno(SoftDeleteMixin, TimestampMixin, Base):
    """Cita con duración variable y asignación física obligatoria (RN-AG-03).

    `fin` se calcula desde `inicio + duracion_min` (RN-AG-02); C-04 debe usar
    la misma fórmula que exige `ck_turnos_fin_coherente`.
    """

    __tablename__ = "turnos"
    __table_args__ = (
        CheckConstraint("fin > inicio", name="rango"),
        CheckConstraint("duracion_min > 0", name="duracion"),
        CheckConstraint(
            "estado IN ('reservado', 'confirmado', 'presente', 'atendido', 'cancelado',"
            " 'ausente')",
            name="estado",
        ),
        CheckConstraint("sena_monto >= 0", name="sena"),
        CheckConstraint(
            "NOT es_sobreturno OR (motivo_sobreturno IS NOT NULL"
            " AND length(btrim(motivo_sobreturno)) > 0)",
            name="sobreturno_motivo",
        ),
        CheckConstraint(
            "fin = inicio + (duracion_min * interval '1 minute')", name="fin_coherente"
        ),
        UniqueConstraint("token_publico", name="token_publico"),
        Index("ix_turnos_sillon_inicio_fin", "sillon_id", "inicio", "fin"),
        Index("ix_turnos_profesional_inicio_fin", "profesional_id", "inicio", "fin"),
        Index("ix_turnos_inicio", "inicio"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    paciente_id: Mapped[UUID] = mapped_column(
        ForeignKey("pacientes.id", name="fk_turnos_paciente_id_pacientes"), nullable=False
    )
    profesional_id: Mapped[UUID] = mapped_column(
        ForeignKey("profesionales.id", name="fk_turnos_profesional_id_profesionales"), nullable=False
    )
    sillon_id: Mapped[UUID] = mapped_column(
        ForeignKey("sillones.id", name="fk_turnos_sillon_id_sillones"), nullable=False
    )
    prestacion: Mapped[str] = mapped_column(String(150), nullable=False)
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duracion_min: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="reservado", server_default=text("'reservado'")
    )
    token_publico: Mapped[UUID] = mapped_column(
        Uuid, nullable=False, default=uuid4, server_default=text("gen_random_uuid()")
    )
    sena_monto: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00"), server_default=text("0")
    )
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    es_sobreturno: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    motivo_sobreturno: Mapped[str | None] = mapped_column(String(255), nullable=True)
    autorizado_por: Mapped[UUID | None] = mapped_column(
        ForeignKey("usuarios.id", name="fk_turnos_autorizado_por_usuarios"), nullable=True
    )


class Bloqueo(TimestampMixin, Base):
    """Bloqueo temporal de disponibilidad por sillón, profesional o ambos."""

    __tablename__ = "bloqueos"
    __table_args__ = (
        CheckConstraint(
            "sillon_id IS NOT NULL OR profesional_id IS NOT NULL", name="recurso"
        ),
        CheckConstraint("hasta > desde", name="rango"),
        CheckConstraint("length(btrim(motivo)) > 0", name="motivo_no_vacio"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    sillon_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("sillones.id", name="fk_bloqueos_sillon_id_sillones"), nullable=True
    )
    profesional_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("profesionales.id", name="fk_bloqueos_profesional_id_profesionales"),
        nullable=True,
    )
    desde: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hasta: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    motivo: Mapped[str] = mapped_column(String(255), nullable=False)
