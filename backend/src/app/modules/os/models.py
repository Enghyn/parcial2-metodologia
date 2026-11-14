"""Modelos de obras sociales, convenios y afiliación (C-13a)."""
from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    ForeignKey,
    Numeric,
    String,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ObraSocial(TimestampMixin, Base):
    __tablename__ = "obras_sociales"
    __table_args__ = (  # type: ignore[assignment]
        # nombre único
    )

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    codigo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    activo: Mapped[bool] = mapped_column(
        nullable=False, default=True, server_default=text("true")
    )


class Convenio(TimestampMixin, Base):
    __tablename__ = "convenios"

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    obra_social_id: Mapped[UUID] = mapped_column(
        ForeignKey("obras_sociales.id", name="fk_convenios_obra_social_id_obras_sociales"),
        nullable=False,
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    vigente_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vigente_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
    descuento_global: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    activo: Mapped[bool] = mapped_column(
        nullable=False, default=True, server_default=text("true")
    )


class PacienteObraSocial(TimestampMixin, Base):
    __tablename__ = "pacientes_obra_social"

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    paciente_id: Mapped[UUID] = mapped_column(
        ForeignKey("pacientes.id", name="fk_pos_paciente_id_pacientes"), nullable=False
    )
    obra_social_id: Mapped[UUID] = mapped_column(
        ForeignKey("obras_sociales.id", name="fk_pos_obra_social_id_obras_sociales"),
        nullable=False,
    )
    convenio_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("convenios.id", name="fk_pos_convenio_id_convenios"), nullable=True
    )
    nro_afiliado: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vigente_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vigente_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)


# Importar Paciente para que la FK se registre en metadata (ya está en clinica.models)
from app.modules.admin.models import Usuario  # noqa: F401
from app.modules.clinica.models import Paciente  # noqa: F401
