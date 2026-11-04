"""Configuración por entorno (pydantic-settings). R1: schemas API con extra=forbid (ver core/errors + schemas)."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_SECRETO_INSEGURO_PREFIX = "changeme-"


class Settings(BaseSettings):
    """Settings de la app. Falla al arrancar si falta una requerida (spec backend-foundation)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(description="DSN Postgres")
    redis_url: str = Field(default="redis://redis:6379/0")
    jwt_secret: str = Field(default="changeme-32-caracteres-minimo-1234")
    jwt_expire_min: int = Field(default=60)
    cors_origins: str = Field(default="http://localhost:5173")
    app_env: str = Field(default="local")
    public_slot_start: str = Field(default="08:00")
    public_slot_end: str = Field(default="20:00")
    public_slot_grid_min: int = Field(default=30, gt=0)

    @model_validator(mode="after")
    def _rechazar_secreto_jwt_inseguro_en_produccion(self) -> Settings:
        """D5: con APP_ENV=production, un JWT_SECRET con el default inseguro
        (changeme-*) hace fallar el arranque — el secreto debe venir del entorno."""
        if self.app_env == "production" and self.jwt_secret.startswith(_SECRETO_INSEGURO_PREFIX):
            raise ValueError(
                "JWT_SECRET inseguro en production: define JWT_SECRET (32+ caracteres) "
                "en el entorno en lugar del default changeme-*"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]