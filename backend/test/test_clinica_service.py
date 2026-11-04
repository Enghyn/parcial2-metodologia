"""TDD C-07 — servicios de pacientes y odontograma contra PostgreSQL."""
import logging
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_session_factory
from app.modules.clinica.models import HallazgoPieza, Paciente
from app.modules.clinica.schemas import HallazgoIn, PacienteCreate
from app.modules.clinica.service import OdontogramaService, PacienteService

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("db_disponible")]


def _session() -> Session:
    return get_session_factory()()


def _dni() -> str:
    return "C" + uuid4().hex[:12]


def _paciente(session: Session, dni: str | None = None) -> Paciente:
    paciente = Paciente(
        nombre="Paciente Clínica",
        dni=dni or _dni(),
        telefono="1144556677",
        activo=True,
    )
    session.add(paciente)
    session.commit()
    session.refresh(paciente)
    return paciente


def test_listar_excluye_borrados_y_filtra_por_dni() -> None:
    session = _session()
    try:
        paciente = _paciente(session)
        paciente.soft_delete()
        session.commit()
        servicio = PacienteService(session)
        assert all(p.id != paciente.id for p in servicio.listar(q=paciente.dni))
    finally:
        session.close()


def test_crear_rechaza_dni_duplicado() -> None:
    session = _session()
    try:
        dni = _dni()
        servicio = PacienteService(session)
        servicio.crear(PacienteCreate(nombre="Uno", dni=dni, telefono="1"))
        with pytest.raises(HTTPException) as exc:
            servicio.crear(PacienteCreate(nombre="Dos", dni=dni, telefono="2"))
        assert exc.value.status_code == 409
    finally:
        session.close()


def test_odontograma_se_crea_una_sola_vez() -> None:
    session = _session()
    try:
        paciente = _paciente(session)
        servicio = OdontogramaService(session)
        primero = servicio.obtener_o_crear(paciente.id)
        segundo = servicio.obtener_o_crear(paciente.id)
        assert primero.id == segundo.id
        paciente.soft_delete()
        session.commit()
    finally:
        session.close()


def test_odontograma_de_paciente_borrado_404() -> None:
    session = _session()
    try:
        paciente = _paciente(session)
        paciente.soft_delete()
        session.commit()
        with pytest.raises(HTTPException) as exc:
            OdontogramaService(session).obtener_o_crear(paciente.id)
        assert exc.value.status_code == 404
    finally:
        session.close()


def test_upsert_inserta_y_actualiza_la_misma_pieza() -> None:
    session = _session()
    try:
        paciente = _paciente(session)
        servicio = OdontogramaService(session)
        primero = servicio.upsert(paciente.id, 16, HallazgoIn(estado="caries"))
        segundo = servicio.upsert(paciente.id, 16, HallazgoIn(estado="obturacion"))
        assert primero.id == segundo.id
        assert segundo.estado == "obturacion"
        cantidad = session.scalar(
            select(func.count())
            .select_from(HallazgoPieza)
            .where(HallazgoPieza.odontograma_id == primero.odontograma_id)
        )
        assert cantidad == 1
        paciente.soft_delete()
        session.commit()
    finally:
        session.close()


def test_upsert_rechaza_pieza_fuera_de_fdi() -> None:
    session = _session()
    try:
        paciente = _paciente(session)
        with pytest.raises(HTTPException) as exc:
            OdontogramaService(session).upsert(paciente.id, 19, HallazgoIn(estado="caries"))
        assert exc.value.status_code == 422
        paciente.soft_delete()
        session.commit()
    finally:
        session.close()


def test_no_loguea_estado_ni_observacion(caplog) -> None:
    caplog.set_level(logging.DEBUG)
    session = _session()
    try:
        paciente = _paciente(session)
        OdontogramaService(session).upsert(
            paciente.id,
            11,
            HallazgoIn(estado="caries", observacion="Sensibilidad confidencial"),
        )
        propios = [registro.getMessage() for registro in caplog.records if registro.name.startswith("app")]
        assert all("caries" not in mensaje for mensaje in propios)
        assert all("Sensibilidad confidencial" not in mensaje for mensaje in propios)
        paciente.soft_delete()
        session.commit()
    finally:
        session.close()
