"""Modelos de nomenclador de prácticas y aranceles por convenio (C-13a)."""
from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import (
    ForeignKey,
    Numeric,
    String,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.modules.os.models import Convenio  # noqa: F401


class NomencladorPractica(TimestampMixin, Base):
    __tablename__ = "nomenclador_practicas"

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    codigo: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    descripcion: Mapped[str] = mapped_column(String(255), nullable=False)
    arancel_base: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)


class ConvenioPractica(TimestampMixin, Base):
    __tablename__ = "convenio_practicas"
    __table_args__ = (  # type: ignore[assignment]
    )

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    convenio_id: Mapped[UUID] = mapped_column(
        ForeignKey("convenios.id", name="fk_cp_convenio_id_convenios"), nullable=False
    )
    practica_id: Mapped[UUID] = mapped_column(
        ForeignKey("nomenclador_practicas.id", name="fk_cp_practica_id_nomenclador"),
        nullable=False,
    )
    arancel_override: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    copago_fijo: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    copago_porcentaje: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
