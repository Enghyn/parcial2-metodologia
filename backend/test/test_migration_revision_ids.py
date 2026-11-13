"""Guarda de integridad de las migraciones Alembic.

Regresión de un fallo real: el revision id `0008_caja_cierre_cuenta_corriente`
tenía 33 caracteres, pero Alembic crea `alembic_version.version_num` como
`varchar(32)`. SQLite (tests) no valida el largo, Postgres sí: `alembic upgrade
head` fallaba en 0008 con `StringDataRightTruncation` y hacía rollback de todo.
"""
import re
from pathlib import Path

VERSIONS = Path(__file__).resolve().parents[1] / "src" / "app" / "db" / "migrations" / "versions"

# Límite del `alembic_version.version_num` por defecto (varchar(32)).
MAX_REVISION_LEN = 32

_PATRON_REVISION = re.compile(r'^revision(?::\s*str)?\s*=\s*"([^"]+)"', re.MULTILINE)
_PATRON_DOWN = re.compile(r'^down_revision[^=]*=\s*(?:"([^"]+)"|None)', re.MULTILINE)


def _migraciones() -> list[tuple[str, str | None]]:
    """Devuelve [(revision, down_revision)] de todos los archivos de versión."""
    resultado: list[tuple[str, str | None]] = []
    for archivo in sorted(VERSIONS.glob("*.py")):
        if archivo.name.startswith("__"):
            continue
        texto = archivo.read_text(encoding="utf-8")
        revision = _PATRON_REVISION.search(texto)
        assert revision is not None, f"{archivo.name}: no se pudo leer `revision`"
        down = _PATRON_DOWN.search(texto)
        assert down is not None, f"{archivo.name}: no se pudo leer `down_revision`"
        resultado.append((revision.group(1), down.group(1)))
    return resultado


def test_hay_migraciones() -> None:
    assert len(_migraciones()) >= 14


def test_revision_ids_caben_en_varchar_32() -> None:
    largos = {rev: len(rev) for rev, _ in _migraciones()}
    excedidos = {rev: n for rev, n in largos.items() if n > MAX_REVISION_LEN}
    assert excedidos == {}, (
        f"revision ids más largos que {MAX_REVISION_LEN} chars rompen `alembic upgrade` "
        f"en PostgreSQL porque alembic_version.version_num es varchar(32): {excedidos}"
    )


def test_cadena_de_migraciones_integra() -> None:
    migraciones = _migraciones()
    revisiones = {rev for rev, _ in migraciones}
    huerfanos = {rev: down for rev, down in migraciones if down is not None and down not in revisiones}
    assert huerfanos == {}, f"down_revision apunta a revisiones inexistentes: {huerfanos}"


def test_un_solo_head() -> None:
    migraciones = _migraciones()
    referenciadas = {down for _, down in migraciones if down is not None}
    heads = [rev for rev, _ in migraciones if rev not in referenciadas]
    assert len(heads) == 1, f"se esperaba un único head, se encontraron: {heads}"
