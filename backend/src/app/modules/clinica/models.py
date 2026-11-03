"""Modelos de ficha clínica y odontograma FDI (C-02 core-models-seed)."""
from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin

ESTADOS_PIEZA: tuple[str, ...] = (
    "sano",
    "caries",
    "obturacion",
    "corona",
    "extraccion",
    "tratamiento_conducto",
)


class Paciente(SoftDeleteMixin, TimestampMixin, Base):
    """Ficha básica del paciente; el DNI es la clave natural para la reserva pública."""

    __tablename__ = "pacientes"
    __table_args__ = (UniqueConstraint("dni", name="dni"),)

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    dni: Mapped[str] = mapped_column(String(20), nullable=False)
    telefono: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    obra_social: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nro_afiliado: Mapped[str | None] = mapped_column(String(50), nullable=True)
    activo: Mapped[bool] = mapped_column(
        nullable=False, default=True, server_default=text("true")
    )


class Odontograma(TimestampMixin, Base):
    """Cabecera del odontograma: como máximo uno por paciente."""

    __tablename__ = "odontogramas"
    __table_args__ = (UniqueConstraint("paciente_id", name="paciente_id"),)

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    paciente_id: Mapped[UUID] = mapped_column(
        ForeignKey("pacientes.id", name="fk_odontogramas_paciente_id_pacientes"), nullable=False
    )
    observaciones_generales: Mapped[str | None] = mapped_column(Text, nullable=True)


class HallazgoPieza(TimestampMixin, Base):
    """Hallazgo clínico por pieza dental con nomenclatura FDI (11 a 48)."""

    __tablename__ = "hallazgos_pieza"
    __table_args__ = (
        UniqueConstraint("odontograma_id", "pieza", name="odontograma_pieza"),
        CheckConstraint(
            "pieza BETWEEN 11 AND 48 AND pieza % 10 BETWEEN 1 AND 8", name="pieza_fdi"
        ),
        CheckConstraint(
            "estado IN ('sano', 'caries', 'obturacion', 'corona', 'extraccion',"
            " 'tratamiento_conducto')",
            name="estado",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    odontograma_id: Mapped[UUID] = mapped_column(
        ForeignKey("odontogramas.id", name="fk_hallazgos_pieza_odontograma_id_odontogramas"),
        nullable=False,
    )
    pieza: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False)
    observacion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
