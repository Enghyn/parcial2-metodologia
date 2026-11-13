"""C-12b: `cierres_caja.estado` pasa de ENUM nativo a varchar(20) + CHECK.

La migración `0008_caja_cierre_cta_cte` creó la columna con
`sa.Enum(..., name="estado_cierre")`, pero el modelo `CierreCaja` la declara como
`String(20)` con `CheckConstraint("estado IN (...)", name="estado")`. Contra
PostgreSQL real, filtrar por estado fallaba con
`UndefinedFunction: el operador no existe: estado_cierre = character varying`.

Esta migración alinea la base con el modelo y con el resto del esquema
(`turnos`, `hallazgos_pieza`, `usuarios`), que usan varchar + CHECK en lugar de
tipos ENUM nativos. No toca datos, triggers ni la lógica append-only (R3/R13).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015_cierres_estado_varchar"
down_revision: str | None = "0014_pagos_simulados"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Convierte la columna a varchar(20) + CHECK y elimina el tipo `estado_cierre`."""
    # 1. Quitamos el default del ENUM antes del cast: PostgreSQL no puede
    #    convertirlo automáticamente a varchar y abortaría el ALTER TYPE.
    op.alter_column(
        "cierres_caja",
        "estado",
        existing_type=sa.Enum("pendiente", "cerrado", "reabierto", name="estado_cierre"),
        server_default=None,
    )

    # 2. Cambiamos el tipo casteando explícitamente cada valor a texto.
    op.alter_column(
        "cierres_caja",
        "estado",
        existing_type=sa.Enum("pendiente", "cerrado", "reabierto", name="estado_cierre"),
        type_=sa.String(20),
        postgresql_using="estado::text",
    )

    # 3. Restablecemos el default como texto, igual que el modelo.
    op.alter_column(
        "cierres_caja",
        "estado",
        existing_type=sa.String(20),
        server_default="pendiente",
    )

    # 4. Ya no queda ninguna columna que use el tipo: lo borramos del catálogo.
    op.execute("DROP TYPE IF EXISTS estado_cierre")

    # 5. El catálogo pasa a estar garantizado por un CHECK nombrado `estado`.
    op.create_check_constraint(
        "estado",
        "cierres_caja",
        "estado IN ('pendiente', 'cerrado', 'reabierto')",
    )


def downgrade() -> None:
    """Vuelve al ENUM `estado_cierre`, revirtiendo el upgrade en orden inverso."""
    # 1. El CHECK del catálogo no aplica al tipo ENUM que vamos a recrear.
    op.drop_constraint("estado", "cierres_caja", type_="check")

    # 2. Quitamos el default de texto para poder castear la columna.
    op.alter_column(
        "cierres_caja",
        "estado",
        existing_type=sa.String(20),
        server_default=None,
    )

    # 3. Recreamos el tipo ENUM original, con el mismo catálogo.
    op.execute("CREATE TYPE estado_cierre AS ENUM ('pendiente', 'cerrado', 'reabierto')")

    # 4. Casteamos la columna de vuelta al ENUM; los valores son idénticos.
    op.alter_column(
        "cierres_caja",
        "estado",
        existing_type=sa.String(20),
        type_=sa.Enum("pendiente", "cerrado", "reabierto", name="estado_cierre"),
        postgresql_using="estado::estado_cierre",
    )

    # 5. Restauramos el default original.
    op.alter_column(
        "cierres_caja",
        "estado",
        existing_type=sa.Enum("pendiente", "cerrado", "reabierto", name="estado_cierre"),
        server_default="pendiente",
    )
