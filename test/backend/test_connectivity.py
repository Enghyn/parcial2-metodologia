"""Task 3.4 — conectividad Postgres (btree_gist) y Redis bajo compose.

Se saltean si no hay servicios vivos (p. ej. CI sin compose o máquina sin Docker).
"""
import os

import pytest

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg://odonto:odonto@localhost:5432/odonto")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")


def _pg_viva() -> bool:
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 2})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 — probe: cualquier fallo = PG no disponible
        return False


def _redis_vivo() -> bool:
    try:
        import redis

        return bool(redis.Redis.from_url(REDIS_URL, socket_connect_timeout=2).ping())
    except Exception:  # noqa: BLE001 — probe: cualquier fallo = Redis no disponible
        return False


@pytest.mark.skipif(not _pg_viva(), reason="sin Postgres viva (levantar compose)")
def test_postgres_tiene_btree_gist() -> None:
    from sqlalchemy import create_engine, text

    engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 2})
    with engine.connect() as conn:
        filas = list(conn.execute(text("SELECT 1 FROM pg_extension WHERE extname='btree_gist'")))
    assert filas != [], "falta extensión btree_gist (baseline C-01)"


@pytest.mark.skipif(not _redis_vivo(), reason="sin Redis vivo (levantar compose)")
def test_redis_responde_ping() -> None:
    import redis

    assert redis.Redis.from_url(REDIS_URL, socket_connect_timeout=2).ping() is True
