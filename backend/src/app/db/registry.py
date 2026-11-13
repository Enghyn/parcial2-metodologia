"""Registro central de modelos para Alembic y tests.

Importar este módulo garantiza que las nueve tablas de dominio queden
registradas en `Base.metadata`. Alembic (`migrations/env.py`) y la suite de
tests lo usan como única puerta de entrada al esquema.
"""
from app.db.base import Base
from app.modules.admin import models as _admin_models  # noqa: F401
from app.modules.agenda import models as _agenda_models  # noqa: F401
from app.modules.audit import models as _audit_models  # noqa: F401
from app.modules.caja import models as _caja_models  # noqa: F401
from app.modules.clinica import models as _clinica_models  # noqa: F401
from app.modules.comprobante import models as _comprobante_models  # noqa: F401
from app.modules.lista_espera import models as _lista_espera_models  # noqa: F401
from app.modules.nomenclador import models as _nomenclador_models  # noqa: F401
from app.modules.notificaciones import models as _notificaciones_models  # noqa: F401
from app.modules.os import models as _os_models  # noqa: F401
from app.modules.pagos import models as _pagos_models  # noqa: F401
from app.modules.presupuestos import models as _presupuestos_models  # noqa: F401
from app.modules.public import models as _public_models  # noqa: F401

__all__ = ["Base"]
