"""Task 3.4 — settings por entorno + logging sin PHI (R9)."""
import os

import pytest


def test_settings_cargan_desde_entorno() -> None:
    os.environ["DATABASE_URL"] = "postgresql+psycopg://u:p@localhost:5432/odonto_test"
    from app.core.config import Settings

    settings = Settings()  # type: ignore[call-arg]
    assert settings.database_url.startswith("postgresql")
    assert settings.jwt_expire_min > 0


def test_falta_database_url_falla_nombrando_la_variable() -> None:
    os.environ.pop("DATABASE_URL", None)
    from app.core.config import Settings
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as exc_info:
        Settings()  # type: ignore[call-arg]
    assert "database_url" in str(exc_info.value).lower()
    os.environ["DATABASE_URL"] = "postgresql+psycopg://u:p@localhost:5432/odonto_test"


def test_logs_nunca_incluyen_datos_de_salud() -> None:
    from app.core.logging import redact

    payload = {"dia": "2026-10-07", "diagnostico": "caries pieza 11", "telefono": "+5491112345678"}
    limpio = redact(payload)
    assert limpio["dia"] == "2026-10-07"
    assert limpio["diagnostico"] == "[redacted]"
    assert limpio["telefono"] == "[redacted]"
