"""C-09b: índice B-tree sobre `turnos.inicio` para el listado por rango."""
from collections.abc import Sequence

from alembic import op

revision: str = "0005_agenda_indice_inicio"
down_revision: str | None = "0004_agenda_avanzada"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crea `ix_turnos_inicio` para el filtro global por rango de la agenda.

    El listado semanal filtra `deleted_at IS NULL AND inicio >= X AND
    inicio < Y` y ordena por `inicio`. Los índices existentes arrancan por
    `sillon_id` o `profesional_id`, así que no sirven de prefijo para ese
    acceso; con 2–3 sillones el volumen es bajo, pero el índice evita un
    sequential scan cuando crezca el histórico (D4). Sin cambios de columnas.
    """
    op.create_index("ix_turnos_inicio", "turnos", ["inicio"])


def downgrade() -> None:
    """Elimina el índice; no toca datos ni columnas (reversible, D4)."""
    op.drop_index("ix_turnos_inicio", table_name="turnos")
