"""C-15: lista de espera."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012_lista_espera"
down_revision: str | None = "0011_notificaciones"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lista_espera",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("paciente_id", sa.Uuid(), nullable=False),
        sa.Column("profesional_id", sa.Uuid(), nullable=True),
        sa.Column("sillon_id", sa.Uuid(), nullable=True),
        sa.Column("fecha_preferida", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="pendiente"),
        sa.Column("ofrecido_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], name="fk_le_paciente"),
        sa.ForeignKeyConstraint(["profesional_id"], ["profesionales.id"], name="fk_le_profesional"),
        sa.ForeignKeyConstraint(["sillon_id"], ["sillones.id"], name="fk_le_sillon"),
        sa.PrimaryKeyConstraint("id", name="pk_lista_espera"),
    )


def downgrade() -> None:
    op.drop_table("lista_espera")