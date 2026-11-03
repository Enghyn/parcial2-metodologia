"""Integración opcional del hardening C-02b contra PostgreSQL real.

Se ejecuta solo si `C02_PG_URL` está definida; la suite normal la saltea.
Requiere una base migrada y sembrada (`alembic upgrade head` + `python -m app.db.seed`).
"""
import os
from collections.abc import Sequence

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError, IntegrityError

URL = os.environ.get("C02_PG_URL")
pytestmark = pytest.mark.skipif(not URL, reason="definir C02_PG_URL para la integración")


@pytest.fixture(scope="module", autouse=True)
def _requiere_seed() -> None:
    engine = create_engine(URL or "")
    try:
        with engine.connect() as conn:
            pacientes = conn.execute(text("select count(*) from pacientes")).scalar_one()
    finally:
        engine.dispose()
    if pacientes == 0:
        pytest.skip("ejecutar python -m app.db.seed antes de la integración")


def _esperar_error(statements: Sequence[str], fragmento: str) -> None:
    engine = create_engine(URL or "")
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                for sql in statements:
                    conn.execute(text(sql))
            except (IntegrityError, DBAPIError) as exc:
                assert fragmento in str(exc), str(exc)
            else:
                pytest.fail("la base aceptó una operación que debía rechazar")
            finally:
                trans.rollback()
    finally:
        engine.dispose()


def test_email_con_mayusculas_es_rechazado_por_la_base() -> None:
    _esperar_error(
        [
            """
            INSERT INTO usuarios (id, nombre, email, password_hash, rol)
            VALUES (gen_random_uuid(), 'Test', 'Admin@Test.COM', 'x', 'admin')
            """
        ],
        "ck_usuarios_email_normalizado",
    )


def test_motivo_solo_espacios_es_rechazado() -> None:
    _esperar_error(
        [
            """
            WITH sillon AS (
                INSERT INTO sillones (id, nombre)
                VALUES (gen_random_uuid(), 'Sillón hardening')
                RETURNING id
            )
            INSERT INTO bloqueos (id, sillon_id, desde, hasta, motivo)
            SELECT gen_random_uuid(), id, now(), now() + interval '1 hour', '   '
            FROM sillon
            """
        ],
        "ck_bloqueos_motivo_no_vacio",
    )


def test_fin_incoherente_con_la_duracion_es_rechazado() -> None:
    _esperar_error(
        [
            """
            INSERT INTO turnos (
                id, paciente_id, profesional_id, sillon_id, prestacion,
                inicio, fin, duracion_min
            )
            SELECT gen_random_uuid(), p.id, pr.id, s.id, 'Consulta',
                   timestamptz '2026-11-04 10:00:00-03',
                   timestamptz '2026-11-04 10:45:00-03', 30
            FROM pacientes p, profesionales pr, sillones s
            LIMIT 1
            """
        ],
        "ck_turnos_fin_coherente",
    )


def test_caja_no_admite_update_ni_delete() -> None:
    _esperar_error(
        [
            """
            INSERT INTO usuarios (id, nombre, email, password_hash, rol)
            VALUES (gen_random_uuid(), 'Caja', 'caja-update@test.com', 'x', 'admin')
            """,
            """
            INSERT INTO movimientos_caja (id, tipo, medio_pago, monto, concepto, usuario_id)
            SELECT gen_random_uuid(), 'ingreso', 'efectivo', 100, 'test-caja-update', id
            FROM usuarios WHERE email = 'caja-update@test.com'
            """,
            "UPDATE movimientos_caja SET concepto = 'mutado' WHERE concepto = 'test-caja-update'",
        ],
        "append-only",
    )
    _esperar_error(
        [
            """
            INSERT INTO usuarios (id, nombre, email, password_hash, rol)
            VALUES (gen_random_uuid(), 'Caja', 'caja-delete@test.com', 'x', 'admin')
            """,
            """
            INSERT INTO movimientos_caja (id, tipo, medio_pago, monto, concepto, usuario_id)
            SELECT gen_random_uuid(), 'ingreso', 'efectivo', 100, 'test-caja-delete', id
            FROM usuarios WHERE email = 'caja-delete@test.com'
            """,
            "DELETE FROM movimientos_caja WHERE concepto = 'test-caja-delete'",
        ],
        "append-only",
    )


def test_caja_no_admite_truncate() -> None:
    _esperar_error(["TRUNCATE movimientos_caja"], "append-only")


def test_borrado_logico_no_admite_delete_ni_truncate() -> None:
    _esperar_error(
        [
            """
            INSERT INTO pacientes (id, nombre, dni, telefono)
            VALUES (gen_random_uuid(), 'Test', '99887766', '1')
            """,
            "DELETE FROM pacientes WHERE dni = '99887766'",
        ],
        "borrado logico",
    )
    _esperar_error(["TRUNCATE pacientes CASCADE"], "borrado logico")
