"""C-13b: comprobante manual."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_comprobante_manual"
down_revision: str | None = "0009_os_nomenclador_cobertura"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "comprobantes",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("numero", sa.String(50), nullable=False),
        sa.Column("movimiento_id", sa.Uuid(), nullable=True),
        sa.Column("presupuesto_id", sa.Uuid(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="pendiente"),
        sa.Column("emitido_por", sa.Uuid(), nullable=True),
        sa.Column("emitido_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("anulado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["movimiento_id"], ["movimientos_caja.id"], name="fk_comp_movimiento"),
        sa.ForeignKeyConstraint(["emitido_por"], ["usuarios.id"], name="fk_comp_emitido_por"),
        sa.PrimaryKeyConstraint("id", name="pk_comprobantes"),
        sa.UniqueConstraint("numero", name="uq_comprobantes_numero"),
    )


def downgrade() -> None:
    op.drop_table("comprobantes")