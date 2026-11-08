"""C-12: cierre diario, cuenta corriente y ajustes auditados.

Tablas:
- `cierres_caja`: cierre diario aprobado por admin, balance, bloqueo de período.
- `cuentas_corrientes_paciente`: saldo derivado por paciente de sus movimientos.
- `ajustes_caja`: contra-asientos auditados vinculados al movimiento original.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_caja_cierre_cuenta_corriente"
down_revision: str | None = "0007_ficha_clinica_avanzada"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Tablas nuevas ---

    # Tabla cierres_caja (D1): cierre diario aprobado por admin
    op.create_table(
        "cierres_caja",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column(
            "fecha_dia",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "estado",
            sa.Enum("pendiente", "cerrado", "reabierto", name="estado_cierre"),
            nullable=False,
            server_default="pendiente",
        ),
        sa.Column(
            "balance",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "total_ingresos",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "total_egresos",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "aprobado_por",
            sa.Uuid(),
            nullable=True,
        ),
        sa.Column(
            "aprobado_en",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_cierres_caja"),
        sa.UniqueConstraint("fecha_dia", name="uq_cierres_caja_fecha_dia"),
    )
    op.create_index(
        "ix_cierres_caja_fecha_dia",
        "cierres_caja",
        ["fecha_dia"],
        postgresql_using="btree",
    )

    # Tabla cuentas_corrientes_paciente (D2): saldo derivado por paciente
    op.create_table(
        "cuentas_corrientes_paciente",
        sa.Column(
            "paciente_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "saldo",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "actualizado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("paciente_id", name="pk_cuentas_corrientes_paciente"),
        sa.UniqueConstraint("paciente_id", name="uq_cuentas_corrientes_paciente_paciente_id"),
    )
    op.create_index(
        "ix_cuentas_corrientes_paciente_saldo",
        "cuentas_corrientes_paciente",
        ["saldo"],
        postgresql_using="btree",
    )

    # Tabla ajustes_caja (D3): contra-asientos auditados
    op.create_table(
        "ajustes_caja",
        sa.Column(
            "id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column(
            "movimiento_corregido_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "movimiento_ajuste_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "motivo",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "fecha",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "usuario_aprobador_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["movimiento_corregido_id"],
            ["movimientos_caja.id"],
            name="fk_ajustes_corregido_id_movimientos",
        ),
        sa.ForeignKeyConstraint(
            ["movimiento_ajuste_id"],
            ["movimientos_caja.id"],
            name="fk_ajustes_ajuste_id_movimientos",
        ),
        sa.ForeignKeyConstraint(
            ["usuario_aprobador_id"],
            ["usuarios.id"],
            name="fk_ajustes_aprobador_id_usuarios",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ajustes_caja"),
    )
    op.create_index(
        "ix_ajustes_caja_movimiento_corregido",
        "ajustes_caja",
        ["movimiento_corregido_id"],
        postgresql_using="btree",
    )
    op.create_index(
        "ix_ajustes_caja_movimiento_ajuste",
        "ajustes_caja",
        ["movimiento_ajuste_id"],
        postgresql_using="btree",
    )

    # --- Triggers de inmutabilidad para las nuevas tablas ---
    # Para ajustes_caja: bloquear UPDATE/DELETE (append-only, R13/RN-CJ-02)
    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_ajustes_no_modificar()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'No se puede modificar ni borrar filas de ajustes_caja (append-only, R13/D3)';
            RETURN NULL;
        END;
        $$;
        """
    )
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_ajustes_no_modificar ON ajustes_caja;
        CREATE TRIGGER trg_ajustes_no_modificar
        BEFORE UPDATE OR DELETE ON ajustes_caja
        FOR EACH ROW
        EXECUTE FUNCTION fn_ajustes_no_modificar();
        """
    )

    # Para cierres_caja: bloquear UPDATE/DELETE (append-only contable)
    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_cierres_no_modificar()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'No se puede modificar ni borrar filas de cierres_caja (append-only contable)';
            RETURN NULL;
        END;
        $$;
        """
    )
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_cierres_no_modificar ON cierres_caja;
        CREATE TRIGGER trg_cierres_no_modificar
        BEFORE UPDATE OR DELETE ON cierres_caja
        FOR EACH ROW
        EXECUTE FUNCTION fn_cierres_no_modificar();
        """
    )


def downgrade() -> None:
    # Borrar triggers primero
    op.execute(f"DROP TRIGGER IF EXISTS trg_ajustes_no_modificar ON ajustes_caja")
    op.execute(f"DROP FUNCTION IF EXISTS fn_ajustes_no_modificar()")
    op.execute(f"DROP TRIGGER IF EXISTS trg_cierres_no_modificar ON cierres_caja")
    op.execute(f"DROP FUNCTION IF EXISTS fn_cierres_no_modificar()")

    # Borrar índices y tablas en orden inverso
    op.drop_index("ix_ajustes_caja_movimiento_ajuste", table_name="ajustes_caja")
    op.drop_index("ix_ajustes_caja_movimiento_corregido", table_name="ajustes_caja")
    op.drop_table("ajustes_caja")

    op.drop_index("ix_cuentas_corrientes_paciente_saldo", table_name="cuentas_corrientes_paciente")
    op.drop_table("cuentas_corrientes_paciente")

    op.drop_index("ix_cierres_caja_fecha_dia", table_name="cierres_caja")
    op.drop_table("cierres_caja")