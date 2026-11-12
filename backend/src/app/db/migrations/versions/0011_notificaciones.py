"""C-14: notificaciones simuladas."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_notificaciones"
down_revision: str | None = "0010_comprobante_manual"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notificaciones",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("turno_id", sa.Uuid(), nullable=True),
        sa.Column("plantilla", sa.String(50), nullable=False),
        sa.Column("destinatario", sa.String(100), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="pendiente"),
        sa.Column("enviado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["turno_id"], ["turnos.id"], name="fk_notif_turno"),
        sa.PrimaryKeyConstraint("id", name="pk_notificaciones"),
    )


def downgrade() -> None:
    op.drop_table("notificaciones")