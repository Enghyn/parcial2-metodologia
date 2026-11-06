"""Tests de modelos de ficha clínica avanzada (C-11, R2, R13).

RED: estos tests deben fallar porque las tablas y columnas nuevas no existen.
"""
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.db.session import get_session_factory
from app.modules.clinica.models import (
    ConsentimientoInformado,
    EvolucionClinica,
    HallazgoPiezaHistorial,
)

pytestmark = []


def _session() -> Session:
    return get_session_factory()()


def test_tabla_evoluciones_clinicas_existe():
    session = _session()
    try:
        inspector = inspect(session.get_bind())
        assert "evoluciones_clinicas" in inspector.get_table_names()
    finally:
        session.close()


def test_tabla_consentimientos_informados_existe():
    session = _session()
    try:
        inspector = inspect(session.get_bind())
        assert "consentimientos_informados" in inspector.get_table_names()
    finally:
        session.close()


def test_tabla_hallazgos_pieza_historial_existe():
    session = _session()
    try:
        inspector = inspect(session.get_bind())
        assert "hallazgos_pieza_historial" in inspector.get_table_names()
    finally:
        session.close()


def test_hallazgos_pieza_tiene_autor_usuario_id():
    session = _session()
    try:
        inspector = inspect(session.get_bind())
        columnas = {c["name"] for c in inspector.get_columns("hallazgos_pieza")}
        assert "autor_usuario_id" in columnas
    finally:
        session.close()


def test_modelos_importables():
    assert EvolucionClinica is not None
    assert ConsentimientoInformado is not None
    assert HallazgoPiezaHistorial is not None


def test_ninguna_tabla_nueva_tiene_tenant_id():
    session = _session()
    try:
        inspector = inspect(session.get_bind())
        for tabla in (
            "evoluciones_clinicas",
            "consentimientos_informados",
            "hallazgos_pieza_historial",
        ):
            columnas = {c["name"] for c in inspector.get_columns(tabla)}
            assert "tenant_id" not in columnas, f"{tabla} no debe tener tenant_id (R2)"
    finally:
        session.close()
