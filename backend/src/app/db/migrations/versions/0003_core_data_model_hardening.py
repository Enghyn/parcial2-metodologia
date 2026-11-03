"""C-02b: hardening del contrato de datos.

Agrega tres constraints y defensas en base para R3 (caja append-only) y R13
(borrado lógico). Los triggers cubren SQL directo y `TRUNCATE`, que no dispara
triggers de fila. Las guardas ORM de `app/db/base.py` se mantienen.
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0003_core_data_model_hardening"
down_revision: str | None = "0002_core_models"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE usuarios ADD CONSTRAINT ck_usuarios_email_normalizado "
        "CHECK (email = lower(btrim(email)))"
    )
    op.execute(
        "ALTER TABLE bloqueos ADD CONSTRAINT ck_bloqueos_motivo_no_vacio "
        "CHECK (length(btrim(motivo)) > 0)"
    )
    op.execute(
        "ALTER TABLE turnos ADD CONSTRAINT ck_turnos_fin_coherente "
        "CHECK (fin = inicio + (duracion_min * interval '1 minute'))"
    )

    op.execute(
        """
CREATE OR REPLACE FUNCTION fn_forbid_ledger_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'movimientos_caja es append-only (R3/RN-CJ-02): %', TG_OP;
END;
$$;
"""
    )
    op.execute(
        """
CREATE OR REPLACE FUNCTION fn_forbid_physical_delete()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION '% usa borrado logico (R13/RN-SEG-02): %', TG_TABLE_NAME, TG_OP;
END;
$$;
"""
    )

    op.execute(
        """
CREATE TRIGGER trg_movimientos_caja_inmutable
    BEFORE UPDATE OR DELETE ON movimientos_caja
    FOR EACH ROW EXECUTE FUNCTION fn_forbid_ledger_mutation();
"""
    )
    op.execute(
        """
CREATE TRIGGER trg_movimientos_caja_no_truncate
    BEFORE TRUNCATE ON movimientos_caja
    FOR EACH STATEMENT EXECUTE FUNCTION fn_forbid_ledger_mutation();
"""
    )

    op.execute(
        """
CREATE TRIGGER trg_pacientes_no_delete
    BEFORE DELETE ON pacientes
    FOR EACH ROW EXECUTE FUNCTION fn_forbid_physical_delete();
"""
    )
    op.execute(
        """
CREATE TRIGGER trg_pacientes_no_truncate
    BEFORE TRUNCATE ON pacientes
    FOR EACH STATEMENT EXECUTE FUNCTION fn_forbid_physical_delete();
"""
    )
    op.execute(
        """
CREATE TRIGGER trg_turnos_no_delete
    BEFORE DELETE ON turnos
    FOR EACH ROW EXECUTE FUNCTION fn_forbid_physical_delete();
"""
    )
    op.execute(
        """
CREATE TRIGGER trg_turnos_no_truncate
    BEFORE TRUNCATE ON turnos
    FOR EACH STATEMENT EXECUTE FUNCTION fn_forbid_physical_delete();
"""
    )
    op.execute(
        """
CREATE TRIGGER trg_profesionales_no_delete
    BEFORE DELETE ON profesionales
    FOR EACH ROW EXECUTE FUNCTION fn_forbid_physical_delete();
"""
    )
    op.execute(
        """
CREATE TRIGGER trg_profesionales_no_truncate
    BEFORE TRUNCATE ON profesionales
    FOR EACH STATEMENT EXECUTE FUNCTION fn_forbid_physical_delete();
"""
    )
    op.execute(
        """
CREATE TRIGGER trg_sillones_no_delete
    BEFORE DELETE ON sillones
    FOR EACH ROW EXECUTE FUNCTION fn_forbid_physical_delete();
"""
    )
    op.execute(
        """
CREATE TRIGGER trg_sillones_no_truncate
    BEFORE TRUNCATE ON sillones
    FOR EACH STATEMENT EXECUTE FUNCTION fn_forbid_physical_delete();
"""
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_movimientos_caja_inmutable ON movimientos_caja")
    op.execute("DROP TRIGGER IF EXISTS trg_movimientos_caja_no_truncate ON movimientos_caja")
    op.execute("DROP TRIGGER IF EXISTS trg_pacientes_no_delete ON pacientes")
    op.execute("DROP TRIGGER IF EXISTS trg_pacientes_no_truncate ON pacientes")
    op.execute("DROP TRIGGER IF EXISTS trg_turnos_no_delete ON turnos")
    op.execute("DROP TRIGGER IF EXISTS trg_turnos_no_truncate ON turnos")
    op.execute("DROP TRIGGER IF EXISTS trg_profesionales_no_delete ON profesionales")
    op.execute("DROP TRIGGER IF EXISTS trg_profesionales_no_truncate ON profesionales")
    op.execute("DROP TRIGGER IF EXISTS trg_sillones_no_delete ON sillones")
    op.execute("DROP TRIGGER IF EXISTS trg_sillones_no_truncate ON sillones")

    op.execute("DROP FUNCTION IF EXISTS fn_forbid_physical_delete()")
    op.execute("DROP FUNCTION IF EXISTS fn_forbid_ledger_mutation()")

    op.execute("ALTER TABLE turnos DROP CONSTRAINT IF EXISTS ck_turnos_fin_coherente")
    op.execute("ALTER TABLE bloqueos DROP CONSTRAINT IF EXISTS ck_bloqueos_motivo_no_vacio")
    op.execute("ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS ck_usuarios_email_normalizado")
