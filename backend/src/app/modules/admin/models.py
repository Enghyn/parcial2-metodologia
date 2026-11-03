"""Modelos de identidad y acceso (C-02 core-models-seed)."""
from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, String, UniqueConstraint, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.db.base import Base, TimestampMixin

ROLES_USUARIO: tuple[str, ...] = ("admin", "recepcion", "odontologo")


class Usuario(TimestampMixin, Base):
    """Personal interno del consultorio (DD-02: mono-tenant, sin tenant_id)."""

    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("email", name="email"),
        CheckConstraint("rol IN ('admin', 'recepcion', 'odontologo')", name="rol"),
        CheckConstraint("email = lower(btrim(email))", name="email_normalizado"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid4, server_default=text("gen_random_uuid()")
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False)
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )

    @validates("email")
    def _normalizar_email(self, key: str, value: str) -> str:
        """Normaliza el email antes de persistirlo (trim + minúsculas)."""
        return value.strip().lower()
