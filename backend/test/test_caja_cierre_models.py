"""TDD C-12 — modelos de cierre, cuenta corriente y ajustes (sin PostgreSQL)."""

from __future__ import annotations

import app.db.registry  # noqa: F401  (registra los modelos en Base.metadata)
from app.db.base import Base

TABLAS_C12 = {"cierres_caja", "cuentas_corrientes_paciente", "ajustes_caja"}


def _tabla(nombre: str):
    return Base.metadata.tables[nombre]


def test_tablas_c12_estan_registradas() -> None:
    """Las tres tablas de C-12 están en el metadata de SQLAlchemy."""
    for nombre in TABLAS_C12:
        assert nombre in Base.metadata.tables, f"falta tabla {nombre}"


def test_ninguna_tabla_c12_tiene_tenant_id() -> None:
    """R2: mono-consultorio, sin tenant_id en ninguna tabla de C-12."""
    con_tenant = [
        t.name
        for t in Base.metadata.tables.values()
        if t.name in TABLAS_C12 and "tenant_id" in t.c
    ]
    assert con_tenant == [], f"R2: tenant_id prohibido en {con_tenant}"


def test_cierres_caja_columnas_y_constraints() -> None:
    """D1: cierres_caja tiene fecha_dia UNIQUE, estado con check, balance y aprobador."""
    tabla = _tabla("cierres_caja")
    columnas = {c.name for c in tabla.columns}
    esperadas = {
        "id",
        "fecha_dia",
        "estado",
        "balance",
        "total_ingresos",
        "total_egresos",
        "aprobado_por",
        "aprobado_en",
        "created_at",
    }
    assert esperadas <= columnas, f"faltan columnas en cierres_caja: {esperadas - columnas}"
    assert tabla.c["id"].nullable is False
    assert tabla.c["fecha_dia"].nullable is False
    assert tabla.c["estado"].nullable is False
    assert tabla.c["balance"].nullable is False
    assert tabla.c["aprobado_por"].nullable is True  # FK opcional a usuarios
    assert tabla.c["aprobado_en"].nullable is True
    # unique en fecha_dia
    uniques = [
        c
        for c in tabla.constraints
        if c.__class__.__name__ == "UniqueConstraint"
        and {col.name for col in c.columns} == {"fecha_dia"}
    ]
    assert len(uniques) == 1, "fecha_dia debe ser UNIQUE"
    # check constraint de estado
    checks = {
        c.name: str(c.sqltext)
        for c in tabla.constraints
        if c.__class__.__name__ == "CheckConstraint"
    }
    assert "ck_cierres_caja_estado" in checks
    assert "pendiente" in checks["ck_cierres_caja_estado"]
    assert "cerrado" in checks["ck_cierres_caja_estado"]
    assert "reabierto" in checks["ck_cierres_caja_estado"]
    # tipos numéricos con 2 decimales
    assert str(tabla.c["balance"].type) == "NUMERIC(10, 2)"
    assert str(tabla.c["total_ingresos"].type) == "NUMERIC(10, 2)"
    assert str(tabla.c["total_egresos"].type) == "NUMERIC(10, 2)"


def test_cuentas_corrientes_paciente_columnas() -> None:
    """D2: cuentas_corrientes_paciente con paciente_id UNIQUE, saldo y actualizado_en."""
    tabla = _tabla("cuentas_corrientes_paciente")
    columnas = {c.name for c in tabla.columns}
    assert {"paciente_id", "saldo", "actualizado_en"} <= columnas
    assert tabla.c["paciente_id"].nullable is False
    assert tabla.c["saldo"].nullable is False
    assert tabla.c["actualizado_en"].nullable is False
    # paciente_id es PK (y por tanto UNIQUE) — no se declara UniqueConstraint aparte.
    assert tabla.c["paciente_id"].primary_key is True
    # FK a pacientes
    fks = [fk for fk in tabla.foreign_keys]
    pacientes_fk = [fk for fk in fks if "pacientes" in str(fk)]
    assert len(pacientes_fk) == 1, "se espera FK a pacientes"


def test_ajustes_caja_columnas_y_constraints() -> None:
    """D3: ajustes_caja vincula original + contra-asiento, motivo no vacío, aprobador admin."""
    tabla = _tabla("ajustes_caja")
    columnas = {c.name for c in tabla.columns}
    esperadas = {
        "id",
        "movimiento_corregido_id",
        "movimiento_ajuste_id",
        "motivo",
        "fecha",
        "usuario_aprobador_id",
        "created_at",
    }
    assert esperadas <= columnas, f"faltan columnas: {esperadas - columnas}"
    assert tabla.c["movimiento_corregido_id"].nullable is False
    assert tabla.c["movimiento_ajuste_id"].nullable is False
    assert tabla.c["motivo"].nullable is False
    assert tabla.c["usuario_aprobador_id"].nullable is False
    # FKs a movimientos_caja (ambos lados) y usuarios
    fks = [fk for fk in tabla.foreign_keys]
    movimientos_fk = [fk for fk in fks if "movimientos_caja" in str(fk)]
    usuarios_fk = [fk for fk in fks if "usuarios" in str(fk)]
    assert len(movimientos_fk) == 2, "se esperan 2 FKs a movimientos_caja"
    assert len(usuarios_fk) == 1, "se espera 1 FK a usuarios"
    # check: motivo no vacío
    checks = {
        c.name: str(c.sqltext)
        for c in tabla.constraints
        if c.__class__.__name__ == "CheckConstraint"
    }
    assert "ck_ajustes_caja_motivo_no_vacio" in checks
    # check: movimientos distintos
    assert "ck_ajustes_caja_movimientos_distintos" in checks
    # tipo de monto/saldo numérico
    assert str(tabla.c["motivo"].type) == "VARCHAR(255)"


def test_todas_las_pk_son_uuid_con_gen_random_uuid() -> None:
    """R5: PK simple UUID con server_default gen_random_uuid() en tablas C-12."""
    for nombre in TABLAS_C12:
        if nombre == "cuentas_corrientes_paciente":
            # PK derivada de paciente_id (FK), sin gen_random_uuid.
            continue
        tabla = _tabla(nombre)
        pk = list(tabla.primary_key.columns)
        assert len(pk) == 1, f"{nombre}: se espera PK simple"
        from sqlalchemy import Uuid as SAUuid

        assert isinstance(pk[0].type, SAUuid), f"{nombre}.{pk[0].name} debe ser UUID"
        assert "gen_random_uuid()" in str(pk[0].server_default.arg), (
            f"{nombre}.{pk[0].name} debe tener server_default gen_random_uuid()"
        )


def test_cierres_caja_no_tiene_updated_at() -> None:
    """Append-only: cierres_caja no tiene columna updated_at."""
    assert "updated_at" not in _tabla("cierres_caja").c


def test_ajustes_caja_no_tiene_updated_at() -> None:
    """Append-only: ajustes_caja no tiene columna updated_at."""
    assert "updated_at" not in _tabla("ajustes_caja").c


def test_cuentas_saldo_tiene_default_cero() -> None:
    """D2: saldo default 0.00 para cuentas nuevas."""
    assert str(_tabla("cuentas_corrientes_paciente").c["saldo"].server_default.arg) == (
        "0.00"
    )


def test_ajustes_fk_ambos_lados_movimientos_caja() -> None:
    """D3: ambas FKs apuntan a movimientos_caja.id (original y contra-asiento)."""
    tabla = _tabla("ajustes_caja")
    targets = {fk.target_fullname for fk in tabla.foreign_keys}
    assert "movimientos_caja.id" in targets
    assert "usuarios.id" in targets
    # Hay exactamente 2 FKs que apuntan a movimientos_caja.id
    movimiento_fks = [
        fk for fk in tabla.foreign_keys if fk.target_fullname == "movimientos_caja.id"
    ]
    assert len(movimiento_fks) == 2, "se esperan 2 FKs a movimientos_caja.id"
