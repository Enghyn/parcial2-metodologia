"""C-10: tabla `pre_reservas` (retención) + columna `turnos.origen`."""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_pre_reserva_origen"
down_revision: str | None = "0005_agenda_indice_inicio"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # create_table("pre_reservas") token unique FK a turnos
    # add_column("turnos", "origen") server_default='interno' nullable=False
    op.create_table(
        "pre_reservas",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("token", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("sillon_id", sa.Uuid(), nullable=False),
        sa.Column("profesional_id", sa.Uuid(), nullable=False),
        sa.Column("prestacion", sa.String(length=150), nullable=False),
        sa.Column("inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fin", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duracion_min", sa.Integer(), nullable=False),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "estado", sa.String(length=20), server_default=sa.text("'vigente'"), nullable=False
        ),
        sa.Column("turno_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["sillon_id"], ["sillones.id"], name="fk_pre_reservas_sillon_id_sillones"
        ),
        sa.ForeignKeyConstraint(
            ["profesional_id"], ["profesionales.id"], name="fk_pre_reservas_profesional_id_profesionales"
        ),
        sa.ForeignKeyConstraint(
            ["turno_id"], ["turnos.id"], name="fk_pre_reservas_turno_id_turnos"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_pre_reservas"),
        sa.UniqueConstraint("token", name="uq_pre_reservas_token"),
        sa.UniqueConstraint("turno_id", name="uq_pre_reservas_turno_id"),
        sa.CheckConstraint(
            "estado IN ('vigente', 'consumida', 'expirada', 'cancelada')",
            name="ck_pre_reservas_estado",
        ),
        sa.CheckConstraint("fin > inicio", name="ck_pre_reservas_rango"),
        sa.CheckConstraint(
            "fin = inicio + (duracion_min * interval '1 minute')",
            name="ck_pre_reservas_fin_coherente",
        ),
    )
    op.create_index("ix_pre_reservas_sillon_inicio_fin", "pre_reservas", ["sillon_id", "inicio", "fin"])
    op.create_index("ix_pre_reservas_profesional_inicio_fin", "pre_reservas", ["profesional_id", "inicio", "fin"])
    op.create_index("ix_pre_reservas_expira_en", "pre_reservas", ["expira_en"])

    op.add_column(
        "turnos",
        sa.Column("origen", sa.String(length=20), server_default=sa.text("'interno'"), nullable=False),
    )
    op.create_check_constraint(
        "ck_turnos_origen", "turnos", "origen IN ('interno', 'publico')"
    )


def downgrade() -> None:
    # drop_column + drop_table
    op.drop_constraint("ck_turnos_origen", "turnos", type_="check")
    op.drop_column("turnos", "origen")
    op.drop_table("pre_reservas")