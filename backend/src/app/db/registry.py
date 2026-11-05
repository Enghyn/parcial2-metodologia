"""Registro central de modelos para Alembic y tests.

Importar este módulo garantiza que las nueve tablas de dominio queden
registradas en `Base.metadata`. Alembic (`migrations/env.py`) y la suite de
tests lo usan como única puerta de entrada al esquema.
"""
from app.db.base import Base
from app.modules.admin import models as _admin_models  # noqa: F401
from app.modules.agenda import models as _agenda_models  # noqa: F401
from app.modules.caja import models as _caja_models  # noqa: F401
from app.modules.clinica import models as _clinica_models  # noqa: F401
from app.modules.public import models as _public_models  # noqa: F401

__all__ = ["Base"]
