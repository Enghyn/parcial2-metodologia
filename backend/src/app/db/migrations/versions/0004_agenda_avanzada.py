"""C-09a: agenda avanzada (sobreturnos, autorizador y estado ausente)."""
from collections.abc import Sequence

from alembic import op

revision: str = "0004_agenda_avanzada"
down_revision: str | None = "0003_core_data_model_hardening"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE turnos ADD COLUMN es_sobreturno BOOLEAN NOT NULL DEFAULT false"
    )
    op.execute("ALTER TABLE turnos ADD COLUMN motivo_sobreturno VARCHAR(255)")
    op.execute("ALTER TABLE turnos ADD COLUMN autorizado_por UUID")
    op.execute(
        "ALTER TABLE turnos ADD CONSTRAINT fk_turnos_autorizado_por_usuarios "
        "FOREIGN KEY (autorizado_por) REFERENCES usuarios(id)"
    )

    op.execute("ALTER TABLE turnos DROP CONSTRAINT IF EXISTS ck_turnos_estado")
    op.execute(
        "ALTER TABLE turnos ADD CONSTRAINT ck_turnos_estado CHECK ("
        "estado IN ('reservado', 'confirmado', 'presente', 'atendido', 'cancelado', 'ausente'))"
    )
    op.execute(
        "ALTER TABLE turnos ADD CONSTRAINT ck_turnos_sobreturno_motivo CHECK ("
        "NOT es_sobreturno OR (motivo_sobreturno IS NOT NULL "
        "AND length(btrim(motivo_sobreturno)) > 0))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE turnos DROP CONSTRAINT IF EXISTS ck_turnos_sobreturno_motivo")
    # Sin el estado nuevo, los ausentes se conservan como cancelados.
    op.execute("UPDATE turnos SET estado = 'cancelado' WHERE estado = 'ausente'")
    op.execute("ALTER TABLE turnos DROP CONSTRAINT IF EXISTS ck_turnos_estado")
    op.execute(
        "ALTER TABLE turnos ADD CONSTRAINT ck_turnos_estado CHECK ("
        "estado IN ('reservado', 'confirmado', 'presente', 'atendido', 'cancelado'))"
    )
    op.execute("ALTER TABLE turnos DROP CONSTRAINT IF EXISTS fk_turnos_autorizado_por_usuarios")
    op.execute("ALTER TABLE turnos DROP COLUMN IF EXISTS autorizado_por")
    op.execute("ALTER TABLE turnos DROP COLUMN IF EXISTS motivo_sobreturno")
    op.execute("ALTER TABLE turnos DROP COLUMN IF EXISTS es_sobreturno")
