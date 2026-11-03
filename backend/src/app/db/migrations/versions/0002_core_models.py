"""C-02: tablas de dominio, constraints e índices.

Encadenada al baseline `0001_baseline`, que habilita `btree_gist`. Esta
migración no crea constraints de exclusión: el antisolapamiento se valida en
la capa de servicios (DD-03, RN-AG-01) y los índices de agenda lo soportan.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_core_models"
down_revision: str | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid() -> sa.Column:
    return sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False)


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "usuarios",
        _uuid(),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("rol", sa.String(length=20), nullable=False),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_usuarios"),
        sa.UniqueConstraint("email", name="uq_usuarios_email"),
        sa.CheckConstraint(
            "rol IN ('admin', 'recepcion', 'odontologo')", name="rol"
        ),
    )

    op.create_table(
        "sillones",
        _uuid(),
        sa.Column("nombre", sa.String(length=50), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_sillones"),
    )

    op.create_table(
        "profesionales",
        _uuid(),
        sa.Column("usuario_id", sa.Uuid(), nullable=True),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("matricula", sa.String(length=50), nullable=False),
        sa.Column("especialidad", sa.String(length=100), nullable=False),
        sa.Column(
            "duracion_default_min", sa.Integer(), server_default=sa.text("30"), nullable=False
        ),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuarios.id"], name="fk_profesionales_usuario_id_usuarios"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_profesionales"),
        sa.UniqueConstraint("usuario_id", name="uq_profesionales_usuario_id"),
        sa.UniqueConstraint("matricula", name="uq_profesionales_matricula"),
        sa.CheckConstraint("duracion_default_min > 0", name="duracion"),
    )

    op.create_table(
        "pacientes",
        _uuid(),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("dni", sa.String(length=20), nullable=False),
        sa.Column("telefono", sa.String(length=30), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=True),
        sa.Column("obra_social", sa.String(length=100), nullable=True),
        sa.Column("nro_afiliado", sa.String(length=50), nullable=True),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_pacientes"),
        sa.UniqueConstraint("dni", name="uq_pacientes_dni"),
    )

    op.create_table(
        "turnos",
        _uuid(),
        sa.Column("paciente_id", sa.Uuid(), nullable=False),
        sa.Column("profesional_id", sa.Uuid(), nullable=False),
        sa.Column("sillon_id", sa.Uuid(), nullable=False),
        sa.Column("prestacion", sa.String(length=150), nullable=False),
        sa.Column("inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fin", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duracion_min", sa.Integer(), nullable=False),
        sa.Column(
            "estado", sa.String(length=20), server_default=sa.text("'reservado'"), nullable=False
        ),
        sa.Column(
            "token_publico",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("sena_monto", sa.Numeric(10, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["paciente_id"], ["pacientes.id"], name="fk_turnos_paciente_id_pacientes"
        ),
        sa.ForeignKeyConstraint(
            ["profesional_id"], ["profesionales.id"], name="fk_turnos_profesional_id_profesionales"
        ),
        sa.ForeignKeyConstraint(["sillon_id"], ["sillones.id"], name="fk_turnos_sillon_id_sillones"),
        sa.PrimaryKeyConstraint("id", name="pk_turnos"),
        sa.UniqueConstraint("token_publico", name="uq_turnos_token_publico"),
        sa.CheckConstraint("fin > inicio", name="rango"),
        sa.CheckConstraint("duracion_min > 0", name="duracion"),
        sa.CheckConstraint(
            "estado IN ('reservado', 'confirmado', 'presente', 'atendido', 'cancelado')",
            name="estado",
        ),
        sa.CheckConstraint("sena_monto >= 0", name="sena"),
    )
    op.create_index(
        "ix_turnos_sillon_inicio_fin", "turnos", ["sillon_id", "inicio", "fin"], unique=False
    )
    op.create_index(
        "ix_turnos_profesional_inicio_fin",
        "turnos",
        ["profesional_id", "inicio", "fin"],
        unique=False,
    )

    op.create_table(
        "bloqueos",
        _uuid(),
        sa.Column("sillon_id", sa.Uuid(), nullable=True),
        sa.Column("profesional_id", sa.Uuid(), nullable=True),
        sa.Column("desde", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hasta", sa.DateTime(timezone=True), nullable=False),
        sa.Column("motivo", sa.String(length=255), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["sillon_id"], ["sillones.id"], name="fk_bloqueos_sillon_id_sillones"
        ),
        sa.ForeignKeyConstraint(
            ["profesional_id"],
            ["profesionales.id"],
            name="fk_bloqueos_profesional_id_profesionales",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_bloqueos"),
        sa.CheckConstraint(
            "sillon_id IS NOT NULL OR profesional_id IS NOT NULL", name="recurso"
        ),
        sa.CheckConstraint("hasta > desde", name="rango"),
    )

    op.create_table(
        "odontogramas",
        _uuid(),
        sa.Column("paciente_id", sa.Uuid(), nullable=False),
        sa.Column("observaciones_generales", sa.Text(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["paciente_id"], ["pacientes.id"], name="fk_odontogramas_paciente_id_pacientes"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_odontogramas"),
        sa.UniqueConstraint("paciente_id", name="uq_odontogramas_paciente_id"),
    )

    op.create_table(
        "hallazgos_pieza",
        _uuid(),
        sa.Column("odontograma_id", sa.Uuid(), nullable=False),
        sa.Column("pieza", sa.Integer(), nullable=False),
        sa.Column("estado", sa.String(length=30), nullable=False),
        sa.Column("observacion", sa.String(length=255), nullable=True),
        sa.Column("fecha", sa.Date(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["odontograma_id"],
            ["odontogramas.id"],
            name="fk_hallazgos_pieza_odontograma_id_odontogramas",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_hallazgos_pieza"),
        sa.UniqueConstraint(
            "odontograma_id", "pieza", name="uq_hallazgos_pieza_odontograma_pieza"
        ),
        sa.CheckConstraint(
            "pieza BETWEEN 11 AND 48 AND pieza % 10 BETWEEN 1 AND 8",
            name="pieza_fdi",
        ),
        sa.CheckConstraint(
            "estado IN ('sano', 'caries', 'obturacion', 'corona', 'extraccion',"
            " 'tratamiento_conducto')",
            name="estado",
        ),
    )

    op.create_table(
        "movimientos_caja",
        _uuid(),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("medio_pago", sa.String(length=20), nullable=False),
        sa.Column("monto", sa.Numeric(10, 2), nullable=False),
        sa.Column("concepto", sa.String(length=255), nullable=False),
        sa.Column("turno_id", sa.Uuid(), nullable=True),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["turno_id"], ["turnos.id"], name="fk_movimientos_caja_turno_id_turnos"
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuarios.id"], name="fk_movimientos_caja_usuario_id_usuarios"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_movimientos_caja"),
        sa.CheckConstraint("monto > 0", name="monto"),
        sa.CheckConstraint("tipo IN ('ingreso', 'egreso')", name="tipo"),
        sa.CheckConstraint(
            "medio_pago IN ('efectivo', 'transferencia', 'debito', 'credito', 'otro')",
            name="medio_pago",
        ),
    )


def downgrade() -> None:
    op.drop_table("movimientos_caja")
    op.drop_table("hallazgos_pieza")
    op.drop_table("odontogramas")
    op.drop_table("bloqueos")
    op.drop_index("ix_turnos_profesional_inicio_fin", table_name="turnos")
    op.drop_index("ix_turnos_sillon_inicio_fin", table_name="turnos")
    op.drop_table("turnos")
    op.drop_table("pacientes")
    op.drop_table("profesionales")
    op.drop_table("sillones")
    op.drop_table("usuarios")
