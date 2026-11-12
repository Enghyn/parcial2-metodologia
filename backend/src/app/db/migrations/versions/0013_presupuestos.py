"""C-16: presupuestos."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013_presupuestos"
down_revision: str | None = "0012_lista_espera"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "presupuestos",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("paciente_id", sa.Uuid(), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="borrador"),
        sa.Column("total", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("token_publico", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("aprobado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], name="fk_pres_paciente"),
        sa.PrimaryKeyConstraint("id", name="pk_presupuestos"),
        sa.UniqueConstraint("token_publico", name="uq_presupuestos_token"),
    )
    op.create_table(
        "items_presupuesto",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("presupuesto_id", sa.Uuid(), nullable=False),
        sa.Column("descripcion", sa.String(255), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("arancel", sa.Numeric(10, 2), nullable=False),
        sa.Column("copago", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["presupuesto_id"], ["presupuestos.id"], name="fk_item_presupuesto"),
        sa.PrimaryKeyConstraint("id", name="pk_items_presupuesto"),
    )


def downgrade() -> None:
    op.drop_table("items_presupuesto")
    op.drop_table("presupuestos")