"""C-17: pagos simulados."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014_pagos_simulados"
down_revision: str | None = "0013_presupuestos"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pagos",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("presupuesto_id", sa.Uuid(), nullable=True),
        sa.Column("monto", sa.Numeric(10, 2), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="pendiente"),
        sa.Column("movimiento_id", sa.Uuid(), nullable=True),
        sa.Column("confirmado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["presupuesto_id"], ["presupuestos.id"], name="fk_pago_presupuesto"),
        sa.ForeignKeyConstraint(["movimiento_id"], ["movimientos_caja.id"], name="fk_pago_movimiento"),
        sa.PrimaryKeyConstraint("id", name="pk_pagos"),
    )
    op.create_table(
        "intentos_pago",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("pago_id", sa.Uuid(), nullable=False),
        sa.Column("resultado", sa.String(20), nullable=False),
        sa.Column("procesado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["pago_id"], ["pagos.id"], name="fk_intento_pago"),
        sa.PrimaryKeyConstraint("id", name="pk_intentos_pago"),
    )


def downgrade() -> None:
    op.drop_table("intentos_pago")
    op.drop_table("pagos")