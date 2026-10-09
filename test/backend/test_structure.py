"""Task 5.x — layout canónico raíz src/test únicas con backend+frontend (R5 snake_case).

Canónico §5 (sustituye §4): todo el código productivo vive DENTRO de raíz `src/`
(`src/backend/app/**` + `src/frontend/**`); todos los tests viven FUERA, en raíz
`test/` (`test/backend/**` + `test/frontend/`). Las carpetas sueltas `backend/` y
`frontend/` como contenedores de código QUEDAN ELIMINADAS. Import root `app.*`
preservada vía `pythonpath = ["src/backend"]`.
"""
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

BACKEND_SRC_DIRS = [
    "src/backend/app/core",
    "src/backend/app/modules/agenda",
    "src/backend/app/modules/lista_espera",
    "src/backend/app/modules/clinica",
    "src/backend/app/modules/caja",
    "src/backend/app/modules/os",
    "src/backend/app/modules/notificaciones",
    "src/backend/app/modules/admin",
    "src/backend/app/adapters",
    "src/backend/app/db",
    "src/backend/app/workers",
]

FRONTEND_DIRS = [
    "src/frontend/app",
    "src/frontend/features",
    "src/frontend/shared",
]

# Rutas donde sí puede haber .py: código bajo src/backend, tests bajo test/.
_PERMITIDOS_PY = {"src", "test", "node_modules", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}


def test_raiz_src_y_test_hermanas_con_backend_y_frontend() -> None:
    assert (ROOT / "src").is_dir(), "falta src/ en raíz"
    assert (ROOT / "test").is_dir(), "falta test/ en raíz"
    for d in ("src/backend", "src/frontend", "test/backend", "test/frontend"):
        assert (ROOT / d).is_dir(), f"falta {d}/"


def test_backend_tree_en_src_backend() -> None:
    missing = [d for d in BACKEND_SRC_DIRS if not (ROOT / d).is_dir()]
    assert missing == [], f"directorios backend faltantes bajo src/backend: {missing}"
    assert (ROOT / "src" / "backend" / "app" / "main.py").is_file(), "falta src/backend/app/main.py"


def test_frontend_tree_en_src_frontend() -> None:
    missing = [d for d in FRONTEND_DIRS if not (ROOT / d).is_dir()]
    assert missing == [], f"directorios frontend faltantes bajo src/frontend: {missing}"
    assert (ROOT / "src" / "frontend" / "main.tsx").is_file(), "falta src/frontend/main.tsx"


def test_test_backend_es_hermana_singular_y_sin_plural() -> None:
    assert (ROOT / "test" / "backend").is_dir(), "falta test/backend/"
    assert (ROOT / "test" / "frontend").is_dir(), "falta test/frontend/"
    assert not (ROOT / "test" / "backend" / "tests").exists(), "prohibido tests/ plural"
    suite = list((ROOT / "test" / "backend").glob("test_*.py"))
    assert suite != [], "test/backend/ sin tests"


def test_no_quedan_carpetas_sueltas_backend_frontend_con_codigo() -> None:
    for suelta in ("backend", "frontend"):
        candidata = ROOT / suelta
        assert not candidata.exists(), f"prohibida carpeta suelta con código: {suelta}/"
    for vieja in ("backend/src", "backend/test", "backend/tests", "frontend/src", "frontend/test"):
        assert not (ROOT / vieja).exists(), f"prohibida ubicación vieja: {vieja}"


def test_ningun_py_productivo_fuera_de_src_backend() -> None:
    fuera = sorted(
        str(p.relative_to(ROOT))
        for p in ROOT.rglob("*.py")
        if "__pycache__" not in p.parts
        and ".pytest_cache" not in p.parts
        and ".ruff_cache" not in p.parts
        and "node_modules" not in p.parts
        and ".venv" not in p.parts
        and "openspec" not in p.parts
        and "knowledge-base" not in p.parts
        and ".agents" not in p.parts
        and p.relative_to(ROOT).parts[:2] != ("src", "backend")
        and p.relative_to(ROOT).parts[:1] != ("test",)
    )
    assert fuera == [], f".py fuera de src/backend/ o test/: {fuera}"


def test_pyproject_apunta_a_test_backend_y_src_backend() -> None:
    with (ROOT / "pyproject.toml").open("rb") as fh:
        ini = tomllib.load(fh)["tool"]["pytest"]["ini_options"]
    assert ini["testpaths"] == ["test/backend"], f"testpaths debe ser ['test/backend']: {ini['testpaths']}"
    assert ini.get("pythonpath") == ["src/backend"], (
        f"pythonpath debe ser ['src/backend'] (import root app.*): {ini.get('pythonpath')}"
    )


def test_alembic_apunta_a_src_backend() -> None:
    texto = (ROOT / "alembic.ini").read_text(encoding="utf-8")
    assert "src/backend/app/db/migrations" in texto, "script_location debe apuntar a src/backend"
