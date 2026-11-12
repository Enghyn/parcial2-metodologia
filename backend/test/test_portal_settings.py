"""TDD C-18 tarea 1.2 — `portal_usuario_email` en Settings y `.env.example` (D4/R4).

Capa: unitaria (sin base de datos).
"""
from __future__ import annotations

from pathlib import Path

from app.core.config import Settings

ROOT = Path(__file__).resolve().parents[2]
_DSN = "postgresql+psycopg://u:p@localhost:5432/odonto_test"


def test_portal_usuario_email_tiene_default_del_seed() -> None:
    settings = Settings(DATABASE_URL=_DSN)
    assert settings.portal_usuario_email == "admin@consultorio.com"


def test_portal_usuario_email_se_puede_overridear_por_entorno(monkeypatch) -> None:
    monkeypatch.setenv("PORTAL_USUARIO_EMAIL", "caja.portal@consultorio.com")
    settings = Settings(DATABASE_URL=_DSN)
    assert settings.portal_usuario_email == "caja.portal@consultorio.com"


def test_env_example_documenta_portal_usuario_email() -> None:
    texto = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "PORTAL_USUARIO_EMAIL=" in texto
