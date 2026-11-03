"""Layout KB 08 literal: configs DENTRO de cada lado (R5 snake_case).

Canónico mudanza-completa-configs (opción 2, salda el follow-up de
restructure-por-lado): manifiestos y configs backend en `backend/`
(`backend/pyproject.toml`, `backend/alembic.ini`, `backend/Dockerfile`);
manifiestos y configs frontend en `frontend/` (`frontend/package.json`,
`frontend/tsconfig*.json`, `frontend/vite.config.ts`,
`frontend/eslint.config.js`, `frontend/Dockerfile`). Código backend en
`backend/src/app/**`, tests backend en `backend/test/`; código frontend en
`frontend/src/**`, tests frontend en `frontend/test/`. Import root `app.*`
preservada vía `pythonpath = ["src"]` en `backend/pyproject.toml` (relativo
a `backend/`, cwd canónico `backend/`).

Nota `parents[2]`: este archivo vive en `backend/test/` → parents[0]=test,
parents[1]=backend, parents[2]=raíz. Misma profundidad que antes; verificado
por ejecución (este test corre solo si ROOT resuelve bien).
"""
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

BACKEND_SRC_DIRS = [
    "backend/src/app/core",
    "backend/src/app/modules/agenda",
    "backend/src/app/modules/lista_espera",
    "backend/src/app/modules/clinica",
    "backend/src/app/modules/caja",
    "backend/src/app/modules/os",
    "backend/src/app/modules/notificaciones",
    "backend/src/app/modules/admin",
    "backend/src/app/modules/auth",
    "backend/src/app/adapters",
    "backend/src/app/db",
    "backend/src/app/workers",
]

FRONTEND_DIRS = [
    "frontend/src/app",
    "frontend/src/features",
    "frontend/src/shared",
]

# Setup C-02: core stubs security.py y deps.py dejaron de ser stubs: C-03
# (auth-jwt-roles) los implementa; desde esta change se exige código real.
CORE_STUBS: list[str] = []

ADAPTER_STUBS = [
    "backend/src/app/adapters/facturador.py",
    "backend/src/app/adapters/whatsapp.py",
    "backend/src/app/adapters/mercadopago.py",
]

API_V1_ROUTER = "backend/src/app/api/v1/router.py"

MODULOS = [
    "agenda",
    "lista_espera",
    "clinica",
    "caja",
    "os",
    "notificaciones",
    "admin",
    "auth",
]

MODULO_BARRELS = ["router.py", "service.py", "schemas.py", "models.py"]

# C-02 implementó modelos reales en estos módulos: sus models.py ya no son stubs.
MODULOS_CON_MODELOS = {"admin", "agenda", "clinica", "caja"}

# Auth (C-03) NO duplica la entidad Usuario: el modelo vive en modules/admin
# (D4 de design.md), así que auth no tiene models.py ni stubs que implementar
# (sus barrels son código real de esta misma change).
MODULOS_SIN_MODELOS = {"auth"}
MODULOS_SIN_STUBS = {"auth"}

# Routers con rutas reales ya montadas (C-03 monta auth en /auth); el resto
# nace vacío hasta su change dueño.
MODULOS_CON_RUTAS = {"auth"}


def barrels_de_modulo(modulo: str) -> list[str]:
    """Barrels esperados de un módulo: sin models.py para auth y módulos con modelos."""
    if modulo in MODULOS_CON_MODELOS or modulo in MODULOS_SIN_MODELOS:
        return [b for b in MODULO_BARRELS if b != "models.py"]
    return MODULO_BARRELS


TODOS_LOS_STUBS = (
    CORE_STUBS
    + ADAPTER_STUBS
    + [API_V1_ROUTER]
    + [
        f"backend/src/app/modules/{m}/{b}"
        for m in MODULOS
        if m not in MODULOS_SIN_STUBS
        for b in barrels_de_modulo(m)
    ]
)

BACKEND_MANIFESTS = [
    "backend/pyproject.toml",
    "backend/alembic.ini",
    "backend/Dockerfile",
]

FRONTEND_MANIFESTS = [
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/tsconfig.json",
    "frontend/tsconfig.node.json",
    "frontend/vite.config.ts",
    "frontend/eslint.config.js",
    "frontend/Dockerfile",
]

# Nombres viejos (opción 1): prohibidos en raíz tras la mudanza.
MANIFIESTOS_PROHIBIDOS_EN_RAIZ = [
    "pyproject.toml",
    "alembic.ini",
    "Dockerfile.backend",
    "package.json",
    "package-lock.json",
    "tsconfig.json",
    "tsconfig.node.json",
    "vite.config.ts",
    "eslint.config.js",
    "Dockerfile.frontend",
]


def test_root_resuelve_a_raiz_del_repo() -> None:
    assert (ROOT / "docker-compose.yml").is_file(), f"parents[2] no resuelve a raíz: {ROOT}"
    assert (ROOT / "backend" / "pyproject.toml").is_file(), f"parents[2] no resuelve a raíz: {ROOT}"
    assert (ROOT / "frontend" / "package.json").is_file(), f"parents[2] no resuelve a raíz: {ROOT}"


def test_contenedores_por_lado_con_src_y_test() -> None:
    for d in ("backend", "frontend"):
        assert (ROOT / d).is_dir(), f"falta contenedor {d}/ en raíz"
    for d in ("backend/src", "backend/test", "frontend/src", "frontend/test"):
        assert (ROOT / d).is_dir(), f"falta {d}/"


def test_manifiestos_backend_viven_en_backend() -> None:
    faltan = [f for f in BACKEND_MANIFESTS if not (ROOT / f).is_file()]
    assert faltan == [], f"manifiestos backend faltantes en backend/: {faltan}"


def test_manifiestos_frontend_viven_en_frontend() -> None:
    faltan = [f for f in FRONTEND_MANIFESTS if not (ROOT / f).is_file()]
    assert faltan == [], f"manifiestos frontend faltantes en frontend/: {faltan}"


def test_ningun_manifiesto_de_lado_en_raiz() -> None:
    presentes = [f for f in MANIFIESTOS_PROHIBIDOS_EN_RAIZ if (ROOT / f).exists()]
    assert presentes == [], f"manifiestos de lado en raíz (mudanza incompleta): {presentes}"


def test_backend_tree_en_backend_src() -> None:
    missing = [d for d in BACKEND_SRC_DIRS if not (ROOT / d).is_dir()]
    assert missing == [], f"directorios backend faltantes bajo backend/src: {missing}"
    assert (ROOT / "backend" / "src" / "app" / "main.py").is_file(), "falta backend/src/app/main.py"


def test_frontend_tree_en_frontend_src() -> None:
    missing = [d for d in FRONTEND_DIRS if not (ROOT / d).is_dir()]
    assert missing == [], f"directorios frontend faltantes bajo frontend/src: {missing}"
    assert (ROOT / "frontend" / "src" / "main.tsx").is_file(), "falta frontend/src/main.tsx"
    assert (ROOT / "frontend" / "src" / "index.html").is_file(), "falta frontend/src/index.html (entry)"
    assert not (ROOT / "index.html").exists(), "prohibido index.html en raíz"


def test_backend_test_es_singular_y_sin_plural() -> None:
    assert not (ROOT / "backend" / "test" / "tests").exists(), "prohibido tests/ plural"
    suite = list((ROOT / "backend" / "test").glob("test_*.py"))
    assert suite != [], "backend/test/ sin tests"


def test_no_existen_raices_unicas_src_test_ni_ubicaciones_viejas() -> None:
    for vieja in ("src", "test"):
        assert not (ROOT / vieja).exists(), f"prohibida raíz única: {vieja}/"
    for vieja in ("src/backend", "src/frontend", "test/backend", "test/frontend", "backend/tests"):
        assert not (ROOT / vieja).exists(), f"prohibida ubicación vieja: {vieja}"
    assert not (ROOT / "backend" / "src" / "backend").exists(), "prohibido anidado backend/src/backend"


def test_ningun_py_productivo_fuera_de_backend_src() -> None:
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
        and ".atl" not in p.parts
        and not (len(p.relative_to(ROOT).parts) >= 2 and p.relative_to(ROOT).parts[:2] == ("backend", "src"))
        and not (len(p.relative_to(ROOT).parts) >= 2 and p.relative_to(ROOT).parts[:2] == ("backend", "test"))
    )
    assert fuera == [], f".py fuera de backend/src/ o backend/test/: {fuera}"


def test_pyproject_en_backend_con_paths_relativos() -> None:
    with (ROOT / "backend" / "pyproject.toml").open("rb") as fh:
        ini = tomllib.load(fh)["tool"]["pytest"]["ini_options"]
    assert ini["testpaths"] == ["test"], f"testpaths debe ser ['test'] (relativo a backend/): {ini['testpaths']}"
    assert ini.get("pythonpath") == ["src"], (
        f"pythonpath debe ser ['src'] (import root app.*, relativo a backend/): {ini.get('pythonpath')}"
    )


def test_alembic_ini_en_backend_con_script_relativo() -> None:
    texto = (ROOT / "backend" / "alembic.ini").read_text(encoding="utf-8")
    assert "script_location = src/app/db/migrations" in texto, (
        "script_location debe ser src/app/db/migrations (relativo, cwd canónico backend/)"
    )


def test_vite_root_es_src() -> None:
    texto = (ROOT / "frontend" / "vite.config.ts").read_text(encoding="utf-8")
    assert 'root: "src"' in texto, 'vite root debe ser "src" (entry frontend/src/index.html)'


def test_tsconfig_include_sin_prefijos() -> None:
    import json

    with (ROOT / "frontend" / "tsconfig.json").open(encoding="utf-8") as fh:
        include = json.load(fh)["include"]
    assert include == ["src", "test"], f"tsconfig include debe ser ['src', 'test']: {include}"


def test_eslint_sin_prefijos() -> None:
    texto = (ROOT / "frontend" / "eslint.config.js").read_text(encoding="utf-8")
    assert "frontend/" not in texto, "eslint.config.js no debe tener prefijos frontend/"
    assert "src/**/*.{ts,tsx}" in texto
    assert "src/dist" in texto, "eslint debe ignorar el bundle built en src/dist"


def test_package_json_lint_sin_prefijos() -> None:
    import json

    with (ROOT / "frontend" / "package.json").open(encoding="utf-8") as fh:
        lint = json.load(fh)["scripts"]["lint"]
    assert lint == "eslint src --max-warnings 0", f"lint debe correr sobre src: {lint}"


def test_compose_con_contextos_por_lado() -> None:
    texto = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "Dockerfile.backend" not in texto, "compose no debe nombrar Dockerfile.backend"
    assert "Dockerfile.frontend" not in texto, "compose no debe nombrar Dockerfile.frontend"
    assert "context: backend" in texto
    assert "context: frontend" in texto


def test_core_stubs_existen() -> None:
    faltan = [f for f in CORE_STUBS if not (ROOT / f).is_file()]
    assert faltan == [], f"stubs core faltantes (dueño C-03): {faltan}"


def test_adapters_stubs_existen() -> None:
    faltan = [f for f in ADAPTER_STUBS if not (ROOT / f).is_file()]
    assert faltan == [], f"stubs adapters faltantes (dueños C-07/C-11/C-16): {faltan}"


def test_api_v1_router_agregador_existe() -> None:
    assert (ROOT / API_V1_ROUTER).is_file(), "falta backend/src/app/api/v1/router.py (agregador)"


def test_modulos_tienen_barrels_stub() -> None:
    faltan = [
        f"backend/src/app/modules/{m}/{b}"
        for m in MODULOS
        for b in barrels_de_modulo(m)
        if not (ROOT / "backend" / "src" / "app" / "modules" / m / b).is_file()
    ]
    assert faltan == [], f"barrels por módulo faltantes: {faltan}"


def test_auth_no_duplica_modelo_usuario() -> None:
    """D4: el módulo auth importa Usuario (modules/admin), no tiene models.py (R2)."""
    assert not (ROOT / "backend" / "src" / "app" / "modules" / "auth" / "models.py").exists(), (
        "auth no debe tener models.py: Usuario vive en modules/admin (C-02)"
    )


def test_api_v1_endpoints_prohibido() -> None:
    prohibido = ROOT / "backend" / "src" / "app" / "api" / "v1" / "endpoints"
    assert not prohibido.exists(), "prohibido api/v1/endpoints/ (los routers viven en modules/*/router.py)"


def test_sin_pycache_ni_pyc_versionados() -> None:
    import subprocess

    proc = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    mal = [l for l in proc.stdout.splitlines() if "__pycache__" in l or l.endswith((".pyc", ".pyo"))]
    assert mal == [], f"bytecode versionado (nunca se commitea): {mal}"


def test_stubs_rotulados_con_change_dueno() -> None:
    sin_dueno = [
        f for f in TODOS_LOS_STUBS if (ROOT / f).is_file() and "TODO(C-" not in (ROOT / f).read_text(encoding="utf-8")
    ]
    assert sin_dueno == [], f"stubs sin TODO(C-XX) del change dueño: {sin_dueno}"


def test_schemas_stubs_recuerdan_extra_forbid() -> None:
    sin_r1 = [
        m
        for m in MODULOS
        if 'extra="forbid"' not in (ROOT / "backend" / "src" / "app" / "modules" / m / "schemas.py").read_text(
            encoding="utf-8"
        )
    ]
    assert sin_r1 == [], f"schemas.py sin recordatorio R1 extra=forbid: {sin_r1}"


def test_stubs_importables_y_routers_vacios() -> None:
    import importlib

    from fastapi import APIRouter

    modulos = (
        ["app.core.security", "app.core.deps"]
        + ["app.adapters.facturador", "app.adapters.whatsapp", "app.adapters.mercadopago"]
        + ["app.api.v1.router"]
        + [f"app.modules.{m}.{b[:-3]}" for m in MODULOS for b in barrels_de_modulo(m)]
    )
    for nombre in modulos:
        mod = importlib.import_module(nombre)
        if nombre.endswith(".router"):
            assert isinstance(mod.router, APIRouter), f"{nombre} debe exponer `router: APIRouter`"
            if nombre == "app.api.v1.router":
                # C-03: el agregador ya monta auth; ya no nace vacío.
                assert mod.router.routes != [], "api/v1 debe llevar auth montado (C-03)"
            elif nombre.endswith(".router"):
                prefijo = nombre.split(".")[2]
                if prefijo in MODULOS_CON_RUTAS:
                    assert mod.router.routes != [], f"{nombre} debe declarar sus rutas (change dueña lista)"
                else:
                    assert mod.router.routes == [], f"{nombre}.router debe nacer vacío (sin include_router todavía)"
