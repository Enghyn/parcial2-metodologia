"""conftest: env mínimo para que Settings no falle en tests unitarios."""
import os

import pytest
from sqlalchemy import create_engine, text

from app.core.config import get_settings

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://u:p@localhost:5432/odonto_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
# Secret de test compartido por test_auth_* (C-03): evita el default changeme-*
os.environ.setdefault("JWT_SECRET", "secreto-de-test-de-mas-de-32-caracteres-config")
os.environ.setdefault("JWT_EXPIRE_MIN", "720")


@pytest.fixture(scope="session")
def db_disponible() -> None:
    """Salta los tests de integración si no hay PostgreSQL migrado y sembrado."""
    engine = None
    try:
        engine = create_engine(
            get_settings().database_url,
            connect_args={"connect_timeout": 2},
        )
        with engine.connect() as conn:
            conn.execute(text("select 1"))
            sembrados = conn.execute(text("select count(*) from sillones")).scalar_one()
    except Exception as exc:  # noqa: BLE001  (cualquier fallo de conexión/migración)
        pytest.skip(f"PostgreSQL no disponible o sin migrar: {type(exc).__name__}")
    finally:
        if engine is not None:
            engine.dispose()
    if sembrados == 0:
        pytest.skip("Ejecutá python -m app.db.seed antes de la integración")
