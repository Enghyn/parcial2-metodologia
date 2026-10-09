"""Configuración por entorno (pydantic-settings). R1: schemas API con extra=forbid (ver core/errors + schemas)."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings de la app. Falla al arrancar si falta una requerida (spec backend-foundation)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(description="DSN Postgres")
    redis_url: str = Field(default="redis://redis:6379/0")
    jwt_secret: str = Field(default="changeme-32-caracteres-minimo-1234")
    jwt_expire_min: int = Field(default=60)
    cors_origins: str = Field(default="http://localhost:5173")
    app_env: str = Field(default="local")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
