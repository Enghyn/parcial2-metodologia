"""C-13a: obras sociales, convenios, nomenclador y afiliación."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_os_nomenclador_cobertura"
down_revision: str | None = "0008_caja_cierre_cta_cte"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "obras_sociales",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("codigo", sa.String(50), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_obras_sociales"),
        sa.UniqueConstraint("nombre", name="uq_obras_sociales_nombre"),
    )

    op.create_table(
        "convenios",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("obra_social_id", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("vigente_desde", sa.Date(), nullable=False),
        sa.Column("vigente_hasta", sa.Date(), nullable=True),
        sa.Column("descuento_global", sa.Numeric(5, 2), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["obra_social_id"], ["obras_sociales.id"], name="fk_convenios_obra_social"),
        sa.PrimaryKeyConstraint("id", name="pk_convenios"),
    )

    op.create_table(
        "pacientes_obra_social",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("paciente_id", sa.Uuid(), nullable=False),
        sa.Column("obra_social_id", sa.Uuid(), nullable=False),
        sa.Column("convenio_id", sa.Uuid(), nullable=True),
        sa.Column("nro_afiliado", sa.String(50), nullable=True),
        sa.Column("vigente_desde", sa.Date(), nullable=False),
        sa.Column("vigente_hasta", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], name="fk_pos_paciente"),
        sa.ForeignKeyConstraint(["obra_social_id"], ["obras_sociales.id"], name="fk_pos_obra_social"),
        sa.ForeignKeyConstraint(["convenio_id"], ["convenios.id"], name="fk_pos_convenio"),
        sa.PrimaryKeyConstraint("id", name="pk_pacientes_obra_social"),
    )

    op.create_table(
        "nomenclador_practicas",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("descripcion", sa.String(255), nullable=False),
        sa.Column("arancel_base", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_nomenclador_practicas"),
        sa.UniqueConstraint("codigo", name="uq_nomenclador_codigo"),
    )

    op.create_table(
        "convenio_practicas",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("convenio_id", sa.Uuid(), nullable=False),
        sa.Column("practica_id", sa.Uuid(), nullable=False),
        sa.Column("arancel_override", sa.Numeric(10, 2), nullable=True),
        sa.Column("copago_fijo", sa.Numeric(10, 2), nullable=True),
        sa.Column("copago_porcentaje", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["convenio_id"], ["convenios.id"], name="fk_cp_convenio"),
        sa.ForeignKeyConstraint(["practica_id"], ["nomenclador_practicas.id"], name="fk_cp_practica"),
        sa.PrimaryKeyConstraint("id", name="pk_convenio_practicas"),
        sa.UniqueConstraint("convenio_id", "practica_id", name="uq_cp_convenio_practica"),
    )


def downgrade() -> None:
    op.drop_table("convenio_practicas")
    op.drop_table("nomenclador_practicas")
    op.drop_table("pacientes_obra_social")
    op.drop_table("convenios")
    op.drop_table("obras_sociales")