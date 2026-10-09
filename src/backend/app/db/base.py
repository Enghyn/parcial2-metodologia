"""Base declarativa SQLAlchemy 2.0 (sin tablas de dominio en C-01)."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
