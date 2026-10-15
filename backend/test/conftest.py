"""conftest: env mínimo para que Settings no falle en tests unitarios."""
import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://u:p@localhost:5432/odonto_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
