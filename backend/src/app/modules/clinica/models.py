"""Modelos de ficha clínica y odontograma FDI (C-02 core-models-seed)."""
from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin
from app.modules.admin.models import Usuario  # noqa: F401  (registra tabla usuarios para FK)

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
    autor_usuario_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)


class EvolucionClinica(TimestampMixin, Base):
    """Evolución clínica append-only de un paciente (C-11, D3).

    No hereda SoftDeleteMixin: nunca se borra físicamente. Corrección
    = nueva fila, igual que RN-CJ-02 en caja.
    """

    __tablename__ = "evoluciones_clinicas"
    __table_args__ = (
        CheckConstraint(
            "length(btrim(texto)) > 0", name="evoluciones_texto_no_vacio"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    paciente_id: Mapped[UUID] = mapped_column(
        ForeignKey("pacientes.id", name="fk_evoluciones_paciente_id_pacientes"),
        nullable=False,
    )
    autor_usuario_id: Mapped[UUID] = mapped_column(
        ForeignKey("usuarios.id", name="fk_evoluciones_autor_id_usuarios"),
        nullable=False,
    )
    fecha: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    texto: Mapped[str] = mapped_column(Text, nullable=False)


class ConsentimientoInformado(TimestampMixin, Base):
    """Consentimiento informado versionado (C-11, D4).

    Una fila por versión; nunca se reescribe. UNIQUE(paciente_id, version)
    evita duplicados accidentales.
    """

    __tablename__ = "consentimientos_informados"
    __table_args__ = (
        UniqueConstraint("paciente_id", "version", name="consentimiento_paciente_version"),
        CheckConstraint(
            "length(btrim(version)) > 0", name="consentimiento_version_no_vacia"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    paciente_id: Mapped[UUID] = mapped_column(
        ForeignKey("pacientes.id", name="fk_consentimientos_paciente_id_pacientes"),
        nullable=False,
    )
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    autor_usuario_id: Mapped[UUID] = mapped_column(
        ForeignKey("usuarios.id", name="fk_consentimientos_autor_id_usuarios"),
        nullable=False,
    )


class HallazgoPiezaHistorial(TimestampMixin, Base):
    """Historial append-only de cambios de estado por pieza (C-11, D1).

    Cada upsert de `hallazgos_pieza` inserta una fila aquí con el
    estado/observación anteriores y los nuevos.
    """

    __tablename__ = "hallazgos_pieza_historial"

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    hallazgo_id: Mapped[UUID] = mapped_column(
        ForeignKey("hallazgos_pieza.id", name="fk_historial_hallazgo_id_hallazgos"),
        nullable=False,
    )
    estado_anterior: Mapped[str | None] = mapped_column(String(30), nullable=True)
    estado_nuevo: Mapped[str] = mapped_column(String(30), nullable=False)
    observacion_anterior: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    observacion_nueva: Mapped[str | None] = mapped_column(String(255), nullable=True)
    registrado_en: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    registrado_por: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)

