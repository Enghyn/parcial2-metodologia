"""C-20: tabla `auditorias` para trazabilidad de escrituras sensibles (auditoría).

Encadenada a `0015_cierres_estado_varchar`. Reversible. Sin multi-tenant (R2).
`accion` y `recurso` se controlan con CHECK sobre catálogos cerrados (D3).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0016_auditoria"
down_revision: str | None = "0015_cierres_estado_varchar"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ACCIONES = (
    "'crear', 'actualizar', 'eliminar', 'cancelar', 'reprogramar', 'cerrar', "
    "'reabrir', 'ajustar', 'aprobar', 'cambiar_estado', 'registrar'"
)
_RECURSOS = (
    "'turno', 'bloqueo', 'movimiento_caja', 'movimiento', 'caja', 'cierre_caja', "
    "'cierre', 'ajuste_caja', 'ajuste', 'presupuesto', 'hallazgo_pieza', "
    "'hallazgo', 'odontograma', 'paciente'"
)


def upgrade() -> None:
    op.create_table(
        "auditorias",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=True),
        sa.Column("accion", sa.String(40), nullable=False),
        sa.Column("recurso", sa.String(60), nullable=False),
        sa.Column("recurso_id", sa.Uuid(), nullable=True),
        sa.Column("diff", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuarios.id"], name="fk_auditorias_usuario_id_usuarios", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_auditorias"),
        sa.CheckConstraint(f"accion IN ({_ACCIONES})", name="accion"),
        sa.CheckConstraint(f"recurso IN ({_RECURSOS})", name="recurso"),
    )
    op.create_index("ix_auditorias_fecha", "auditorias", ["fecha"])
    op.create_index("ix_auditorias_recurso_recurso_id", "auditorias", ["recurso", "recurso_id"])
    op.create_index("ix_auditorias_usuario_id", "auditorias", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("ix_auditorias_usuario_id", table_name="auditorias")
    op.drop_index("ix_auditorias_recurso_recurso_id", table_name="auditorias")
    op.drop_index("ix_auditorias_fecha", table_name="auditorias")
    op.drop_table("auditorias")
