"""Task 3.2 — .env.example completos, FACTURADOR_MODO=manual, ARCA_* vacías, sin secretos."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUERIDAS = [
    "DATABASE_URL",
    "REDIS_URL",
    "JWT_SECRET",
    "JWT_EXPIRE_MIN",
    "WA_TOKEN",
    "WA_PHONE_ID",
    "WA_WEBHOOK_VERIFY",
    "MP_ACCESS_TOKEN",
    "MP_WEBHOOK_SECRET",
    "TENANT_DEFAULT_CANCEL_HS",
    "LISTA_ESPERA_OFERTA_MIN",
    "FACTURADOR_MODO",
    "CORS_ORIGINS",
]


def _parse(path: Path) -> dict[str, str]:
    valores: dict[str, str] = {}
    for linea in path.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        valores[clave.strip()] = valor.strip()
    return valores


def test_env_example_raiz_tiene_las_15_variables() -> None:
    valores = _parse(ROOT / ".env.example")
    faltantes = [k for k in REQUERIDAS if k not in valores]
    assert faltantes == [], f"variables faltantes: {faltantes}"
    assert valores["FACTURADOR_MODO"] == "manual"
    assert any(k.startswith("ARCA_") for k in valores), "faltan ARCA_* (fase 2, vacías)"
    for k, v in valores.items():
        if k.startswith("ARCA_"):
            assert v == "", f"{k} debe estar vacía en fase 1"


def test_backend_env_example_existe_y_sin_secretos() -> None:
    valores = _parse(ROOT / ".env.example")
    assert valores["FACTURADOR_MODO"] == "manual"
    texto = (ROOT / ".env.example").read_text(encoding="utf-8")
    for patron in ("EAAB", "APP-", "sk-", "postgresql://u:p@prod"):
        assert patron not in texto, f"posible secreto real: {patron}"
