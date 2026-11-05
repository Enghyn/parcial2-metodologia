"""Contrato de esquema de C-02/C-10: diez tablas, PK UUID, constraints e índices."""
from sqlalchemy import CheckConstraint, UniqueConstraint, Uuid

import app.db.registry  # noqa: F401  (registra los nueve modelos)
from app.db.base import Base
from app.modules.admin.models import Usuario

TABLAS_ESPERADAS = {
    "usuarios",
    "sillones",
    "profesionales",
    "pacientes",
    "turnos",
    "bloqueos",
    "odontogramas",
    "hallazgos_pieza",
    "movimientos_caja",
    "pre_reservas",
}


def _tabla(nombre: str):  # type: ignore[no-untyped-def]
    return Base.metadata.tables[nombre]


def _tiene_unique(tabla, columnas: set[str]) -> bool:  # type: ignore[no-untyped-def]
    for constraint in tabla.constraints:
        if isinstance(constraint, UniqueConstraint) and {c.name for c in constraint.columns} == columnas:
            return True
    return False


def _checks(tabla) -> dict[str, str]:  # type: ignore[no-untyped-def]
    return {
        c.name: str(c.sqltext) for c in tabla.constraints if isinstance(c, CheckConstraint)
    }


def test_existen_exactamente_las_nueve_tablas() -> None:
    assert set(Base.metadata.tables) == TABLAS_ESPERADAS


def test_ninguna_tabla_tiene_tenant_id() -> None:
    con_tenant = [t.name for t in Base.metadata.tables.values() if "tenant_id" in t.c]
    assert con_tenant == [], f"R2: el sistema es mono-consultorio, sobra tenant_id en {con_tenant}"


def test_todas_las_pk_son_uuid_generadas_por_postgres() -> None:
    for tabla in Base.metadata.tables.values():
        pk = list(tabla.primary_key.columns)
        assert len(pk) == 1, f"{tabla.name}: se espera PK simple"
        assert isinstance(pk[0].type, Uuid), f"{tabla.name}.{pk[0].name} debe ser UUID"
        assert "gen_random_uuid()" in str(pk[0].server_default.arg), (
            f"{tabla.name}.{pk[0].name} debe tener server_default gen_random_uuid()"
        )


def test_usuarios() -> None:
    tabla = _tabla("usuarios")
    assert _tiene_unique(tabla, {"email"})
    assert "ck_usuarios_rol" in _checks(tabla)
    for columna in ("nombre", "email", "password_hash", "rol", "activo"):
        assert not tabla.c[columna].nullable, f"usuarios.{columna} no puede ser nulo"
    assert not tabla.c["email"].nullable


def test_profesionales() -> None:
    tabla = _tabla("profesionales")
    assert _tiene_unique(tabla, {"usuario_id"})
    assert _tiene_unique(tabla, {"matricula"})
    assert tabla.c["usuario_id"].nullable is True
    assert "ck_profesionales_duracion" in _checks(tabla)


def test_pacientes() -> None:
    tabla = _tabla("pacientes")
    assert _tiene_unique(tabla, {"dni"})
    assert not tabla.c["telefono"].nullable
    assert tabla.c["email"].nullable is True


def test_turnos_integridad_y_asignacion() -> None:
    tabla = _tabla("turnos")
    checks = _checks(tabla)
    assert "ck_turnos_rango" in checks and "fin > inicio" in checks["ck_turnos_rango"]
    assert "ck_turnos_duracion" in checks
    assert "ck_turnos_estado" in checks
    assert "ck_turnos_sena" in checks
    assert _tiene_unique(tabla, {"token_publico"})
    for fk in ("paciente_id", "profesional_id", "sillon_id"):
        assert not tabla.c[fk].nullable, f"turnos.{fk} es obligatorio (RN-AG-03)"


def test_turnos_indices_de_agenda() -> None:
    indices = {i.name for i in _tabla("turnos").indexes}
    assert "ix_turnos_sillon_inicio_fin" in indices
    assert "ix_turnos_profesional_inicio_fin" in indices


def test_bloqueos() -> None:
    checks = _checks(_tabla("bloqueos"))
    assert "ck_bloqueos_recurso" in checks
    assert "ck_bloqueos_rango" in checks


def test_odontograma_unico_por_paciente() -> None:
    assert _tiene_unique(_tabla("odontogramas"), {"paciente_id"})


def test_hallazgos_pieza_fdi() -> None:
    tabla = _tabla("hallazgos_pieza")
    assert _tiene_unique(tabla, {"odontograma_id", "pieza"})
    checks = _checks(tabla)
    assert "ck_hallazgos_pieza_pieza_fdi" in checks
    assert "BETWEEN 11 AND 48" in checks["ck_hallazgos_pieza_pieza_fdi"]
    assert "ck_hallazgos_pieza_estado" in checks


def test_movimientos_caja() -> None:
    tabla = _tabla("movimientos_caja")
    checks = _checks(tabla)
    assert "ck_movimientos_caja_monto" in checks
    assert "ck_movimientos_caja_tipo" in checks
    assert "ck_movimientos_caja_medio_pago" in checks
    for columna in ("fecha", "tipo", "medio_pago", "monto", "concepto", "usuario_id"):
        assert not tabla.c[columna].nullable, f"movimientos_caja.{columna} es obligatorio (RN-CJ-01)"
    assert "updated_at" not in tabla.c, "el libro append-only no tiene updated_at"


def test_email_se_normaliza_y_es_case_insensitive() -> None:
    usuario = Usuario(
        nombre="Admin",
        email="  Admin@Consultorio.COM  ",
        password_hash="x",
        rol="admin",
    )
    assert usuario.email == "admin@consultorio.com"
    assert "ck_usuarios_email_normalizado" in _checks(_tabla("usuarios"))


def test_bloqueo_rechaza_motivo_vacio() -> None:
    assert "ck_bloqueos_motivo_no_vacio" in _checks(_tabla("bloqueos"))


def test_turno_exige_fin_coherente_con_duracion() -> None:
    checks = _checks(_tabla("turnos"))
    assert "ck_turnos_fin_coherente" in checks
    assert "interval '1 minute'" in checks["ck_turnos_fin_coherente"]


def test_borrado_logico_solo_en_entidades_de_negocio() -> None:
    con_soft_delete = {t.name for t in Base.metadata.tables.values() if "deleted_at" in t.c}
    assert con_soft_delete == {"pacientes", "turnos", "profesionales", "sillones"}
