"""Base declarativa SQLAlchemy 2.0, convenciones y guardas transversales de C-02."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, MetaData, event, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Mapper, mapped_column

from app.core.errors import ImmutableLedgerError, SoftDeleteError

# Nombres estables para constraints e índices (R5: migraciones y tests predecibles).
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base única del proyecto: todas las tablas comparten metadata y convención."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TimestampMixin:
    """`created_at`/`updated_at` con zona horaria en todas las tablas mutables."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SoftDeleteMixin:
    """Borrado lógico para las cuatro entidades de negocio (R13 / RN-SEG-02)."""

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def soft_delete(self) -> None:
        """Marca la entidad como borrada sin perder la fila ni su historial."""
        self.deleted_at = datetime.now(UTC)


class ImmutableLedgerMixin:
    """Marca tablas append-only: no admiten UPDATE ni DELETE (R3 / RN-CJ-02)."""


def _entity_name(target: Any) -> str:
    return type(target).__name__


@event.listens_for(Mapper, "before_delete")
def _reject_physical_delete(mapper: Mapper[Any], connection: Any, target: Any) -> None:
    if isinstance(target, SoftDeleteMixin):
        raise SoftDeleteError(
            f"{_entity_name(target)} usa borrado lógico (deleted_at); prohibido el DELETE físico"
        )


@event.listens_for(Mapper, "before_update")
def _reject_ledger_update(mapper: Mapper[Any], connection: Any, target: Any) -> None:
    if isinstance(target, ImmutableLedgerMixin):
        raise ImmutableLedgerError(
            f"{_entity_name(target)} es append-only; usá un movimiento compensatorio"
        )


@event.listens_for(Mapper, "before_delete")
def _reject_ledger_delete(mapper: Mapper[Any], connection: Any, target: Any) -> None:
    if isinstance(target, ImmutableLedgerMixin):
        raise ImmutableLedgerError(
            f"{_entity_name(target)} es append-only; prohibido el DELETE físico"
        )
