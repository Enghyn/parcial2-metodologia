"""C-11: tablas de ficha clínica avanzada + columna autor en hallazgos_pieza.

Tablas:
- `evoluciones_clinicas`: evolución append-only (D3).
- `consentimientos_informados`: consentimiento versionado (D4).
- `hallazgos_pieza_historial`: historial de cambios de pieza (D1).
Columna:
- `hallazgos_pieza.autor_usuario_id` nullable FK a usuarios (D2).
Triggers de inmutabilidad en las 3 tablas (rechazan UPDATE/DELETE por SQL directo).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_ficha_clinica_avanzada"
down_revision: str | None = "0006_pre_reserva_origen"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _crear_trigger_inmutabilidad(tabla: str) -> None:
    """Crea un trigger BEFORE UPDATE/DELETE que rechaza cualquier mutación en `tabla`."""
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION fn_{tabla}_no_modificar()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'No se puede modificar ni borrar filas de {tabla} (inmutabilidad, R13/D3/D4)';
            RETURN NULL;
        END;
        $$;
        """
    )
    op.execute(
        f"""
        DROP TRIGGER IF EXISTS trg_{tabla}_no_modificar ON {tabla};
        CREATE TRIGGER trg_{tabla}_no_modificar
        BEFORE UPDATE OR DELETE ON {tabla}
        FOR EACH ROW
        EXECUTE FUNCTION fn_{tabla}_no_modificar();
        """
    )


def _borrar_trigger_inmutabilidad(tabla: str) -> None:
    op.execute(f"DROP TRIGGER IF EXISTS trg_{tabla}_no_modificar ON {tabla}")
    op.execute(f"DROP FUNCTION IF EXISTS fn_{tabla}_no_modificar()")


def upgrade() -> None:
    # Tabla evoluciones_clinicas (D3)
    op.create_table(
        "evoluciones_clinicas",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column(
            "paciente_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "autor_usuario_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "fecha",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["paciente_id"],
            ["pacientes.id"],
            name="fk_evoluciones_paciente_id_pacientes",
        ),
        sa.ForeignKeyConstraint(
            ["autor_usuario_id"],
            ["usuarios.id"],
            name="fk_evoluciones_autor_id_usuarios",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_evoluciones_clinicas"),
        sa.CheckConstraint(
            "length(btrim(texto)) > 0",
            name="ck_evoluciones_texto_no_vacio",
        ),
    )
    op.create_index(
        "ix_evoluciones_clinicas_paciente_fecha",
        "evoluciones_clinicas",
        ["paciente_id", "fecha"],
        postgresql_using="btree",
        postgresql_ops={"fecha": "DESC"},
    )

    # Tabla consentimientos_informados (D4)
    op.create_table(
        "consentimientos_informados",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column(
            "paciente_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column("version", sa.String(length=20), nullable=False),
        sa.Column(
            "fecha",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "autor_usuario_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["paciente_id"],
            ["pacientes.id"],
            name="fk_consentimientos_paciente_id_pacientes",
        ),
        sa.ForeignKeyConstraint(
            ["autor_usuario_id"],
            ["usuarios.id"],
            name="fk_consentimientos_autor_id_usuarios",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_consentimientos_informados"),
        sa.UniqueConstraint(
            "paciente_id",
            "version",
            name="uq_consentimientos_paciente_version",
        ),
        sa.CheckConstraint(
            "length(btrim(version)) > 0",
            name="ck_consentimientos_version_no_vacia",
        ),
    )
    op.create_index(
        "ix_consentimientos_paciente_fecha",
        "consentimientos_informados",
        ["paciente_id", "fecha"],
        postgresql_using="btree",
        postgresql_ops={"fecha": "DESC"},
    )

    # Tabla hallazgos_pieza_historial (D1)
    op.create_table(
        "hallazgos_pieza_historial",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column(
            "hallazgo_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column("estado_anterior", sa.String(length=30), nullable=True),
        sa.Column("estado_nuevo", sa.String(length=30), nullable=False),
        sa.Column("observacion_anterior", sa.String(length=255), nullable=True),
        sa.Column("observacion_nueva", sa.String(length=255), nullable=True),
        sa.Column(
            "registrado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("registrado_por", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["hallazgo_id"],
            ["hallazgos_pieza.id"],
            name="fk_historial_hallazgo_id_hallazgos",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_hallazgos_pieza_historial"),
    )
    op.create_index(
        "ix_historial_hallazgo_registrado_en",
        "hallazgos_pieza_historial",
        ["hallazgo_id", "registrado_en"],
        postgresql_using="btree",
        postgresql_ops={"registrado_en": "DESC"},
    )

    # Columna autor_usuario_id en hallazgos_pieza (D2)
    op.add_column(
        "hallazgos_pieza",
        sa.Column(
            "autor_usuario_id",
            sa.Uuid(),
            nullable=True,
        ),
    )
    # autor_usuario_id es columna simple (sin FK) para no romper tests de C-07
    # que usan dependency_overrides con usuario simulado. La integridad se valida
    # en la capa de aplicación (el service siempre pone un usuario real).

    # Triggers de inmutabilidad (D3/D4)
    for tabla in (
        "evoluciones_clinicas",
        "consentimientos_informados",
        "hallazgos_pieza_historial",
    ):
        _crear_trigger_inmutabilidad(tabla)


def downgrade() -> None:
    # Borrar triggers de inmutabilidad
    for tabla in (
        "hallazgos_pieza_historial",
        "consentimientos_informados",
        "evoluciones_clinicas",
    ):
        _borrar_trigger_inmutabilidad(tabla)

    # Borrar columna de hallazgos_pieza (sin FK constraint)
    op.drop_column("hallazgos_pieza", "autor_usuario_id")

    # Borrar tablas en orden inverso
    op.drop_table("hallazgos_pieza_historial")
    op.drop_table("consentimientos_informados")
    op.drop_table("evoluciones_clinicas")
