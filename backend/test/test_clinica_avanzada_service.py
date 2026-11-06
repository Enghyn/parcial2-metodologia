"""Tests de servicio de ficha clínica avanzada (C-11, TDD).

RED: estos tests deben fallar porque EvolucionService y ConsentimientoService
no existen aún.
"""
import logging
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_session_factory
from app.modules.admin.models import Usuario
from app.modules.clinica.models import (
    HallazgoPiezaHistorial,
    Paciente,
)
from app.modules.clinica.schemas import EvolucionCreate, HallazgoIn
from app.modules.clinica.service import (
    ConsentimientoService,
    EvolucionService,
    OdontogramaService,
)

pytestmark = [pytest.mark.integration]


def _session() -> Session:
    return get_session_factory()()


def _usuario_odontologo(session: Session) -> Usuario:
    u = session.scalar(
        select(Usuario).where(Usuario.rol == "odontologo", Usuario.activo.is_(True))
    )
    if u is None:
        raise RuntimeError("No hay odontólogo activo en la base de pruebas")
    return u


def _crear_paciente(session: Session) -> Paciente:
    import time

    dni = str(int(time.time() * 1000) % 100000000)
    paciente = Paciente(
        nombre="Paciente Test",
        dni=dni,
        telefono="1122334455",
        activo=True,
    )
    session.add(paciente)
    session.commit()
    session.refresh(paciente)
    return paciente


def test_crear_evolucion_con_autor():
    session = _session()
    try:
        paciente = _crear_paciente(session)
        autor = _usuario_odontologo(session)
        servicio = EvolucionService(session)
        evo = servicio.crear(
            paciente_id=paciente.id,
            texto="Paciente refiere sensibilidad en pieza 12",
            autor_usuario_id=autor.id,
        )
        assert evo.id is not None
        assert evo.paciente_id == paciente.id
        assert evo.autor_usuario_id == autor.id
        assert evo.texto == "Paciente refiere sensibilidad en pieza 12"
        assert evo.fecha is not None
    finally:
        session.close()


def test_listar_evoluciones_ordenadas_fecha_desc():
    session = _session()
    try:
        paciente = _crear_paciente(session)
        autor = _usuario_odontologo(session)
        servicio = EvolucionService(session)
        servicio.crear(
            paciente_id=paciente.id,
            texto="Evolución 1",
            autor_usuario_id=autor.id,
        )
        servicio.crear(
            paciente_id=paciente.id,
            texto="Evolución 2",
            autor_usuario_id=autor.id,
        )
        lista = servicio.listar(paciente_id=paciente.id)
        assert len(lista) == 2
        assert lista[0].texto == "Evolución 2"
        assert lista[1].texto == "Evolución 1"
        assert lista[0].fecha >= lista[1].fecha
    finally:
        session.close()


def test_evolucion_paciente_borrado_404():
    session = _session()
    try:
        paciente = _crear_paciente(session)
        autor = _usuario_odontologo(session)
        servicio = EvolucionService(session)
        paciente.soft_delete()
        session.commit()
        with pytest.raises(HTTPException) as exc:
            servicio.crear(
                paciente_id=paciente.id,
                texto="Texto de prueba",
                autor_usuario_id=autor.id,
            )
        assert exc.value.status_code == 404
    finally:
        session.close()


def test_evolucion_schema_texto_vacio_rechazado():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        EvolucionCreate(paciente_id=uuid4(), texto="   ")


def test_crear_consentimiento_con_autor():
    session = _session()
    try:
        paciente = _crear_paciente(session)
        autor = _usuario_odontologo(session)
        servicio = ConsentimientoService(session)
        cons = servicio.crear(
            paciente_id=paciente.id,
            version="v1",
            autor_usuario_id=autor.id,
        )
        assert cons.id is not None
        assert cons.paciente_id == paciente.id
        assert cons.version == "v1"
        assert cons.autor_usuario_id == autor.id
    finally:
        session.close()


def test_consentimiento_version_duplicada_409():
    session = _session()
    try:
        paciente = _crear_paciente(session)
        autor = _usuario_odontologo(session)
        servicio = ConsentimientoService(session)
        servicio.crear(paciente_id=paciente.id, version="v1", autor_usuario_id=autor.id)
        with pytest.raises(HTTPException) as exc:
            servicio.crear(
                paciente_id=paciente.id, version="v1", autor_usuario_id=autor.id
            )
        assert exc.value.status_code == 409
    finally:
        session.close()


def test_consentimiento_version_nueva_no_pisa_anterior():
    session = _session()
    try:
        paciente = _crear_paciente(session)
        autor = _usuario_odontologo(session)
        servicio = ConsentimientoService(session)
        cons1 = servicio.crear(
            paciente_id=paciente.id, version="v1", autor_usuario_id=autor.id
        )
        cons2 = servicio.crear(
            paciente_id=paciente.id, version="v2", autor_usuario_id=autor.id
        )
        assert cons1.id != cons2.id
        assert cons1.version == "v1"
        assert cons2.version == "v2"
    finally:
        session.close()


def test_consentimiento_paciente_borrado_404():
    session = _session()
    try:
        paciente = _crear_paciente(session)
        autor = _usuario_odontologo(session)
        servicio = ConsentimientoService(session)
        paciente.soft_delete()
        session.commit()
        with pytest.raises(HTTPException) as exc:
            servicio.crear(
                paciente_id=paciente.id,
                version="v1",
                autor_usuario_id=autor.id,
            )
        assert exc.value.status_code == 404
    finally:
        session.close()


def _crear_odontograma_con_hallazgo(session, paciente_id, pieza=11, estado="sano"):
    servicio = OdontogramaService(session)
    odontograma = servicio.obtener_o_crear(paciente_id)
    hallazgo = servicio.upsert(
        paciente_id=paciente_id,
        pieza=pieza,
        datos=HallazgoIn(estado=estado, observacion="Observación inicial"),
    )
    return odontograma, hallazgo


def test_upsert_guarda_autor_usuario_id():
    session = _session()
    try:
        paciente = _crear_paciente(session)
        autor = _usuario_odontologo(session)
        # Crear odontograma y hallazgo SIN autor (fallará porque upsert no recibe usuario aún)
        servicio = OdontogramaService(session)
        servicio.obtener_o_crear(paciente.id)
        hallazgo = servicio.upsert(
            paciente_id=paciente.id,
            pieza=11,
            datos=HallazgoIn(estado="caries", observacion="Caries oclusal"),
            usuario=autor,
        )
        # Verificar que el hallazgo tiene autor (una vez implementado)
        session.refresh(hallazgo)
        assert hallazgo.autor_usuario_id == autor.id
    finally:
        session.close()


def test_upsert_primera_version_historial_estado_anterior_nulo():
    session = _session()
    try:
        paciente = _crear_paciente(session)
        autor = _usuario_odontologo(session)
        servicio = OdontogramaService(session)
        servicio.obtener_o_crear(paciente.id)
        hallazgo = servicio.upsert(
            paciente_id=paciente.id,
            pieza=12,
            datos=HallazgoIn(estado="caries", observacion="Primera versión"),
            usuario=autor,
        )
        # Verificar que existe una fila en el historial con estado_anterior NULL
        historial = (
            session.scalars(
                __import__("sqlalchemy").select(HallazgoPiezaHistorial).where(
                    HallazgoPiezaHistorial.hallazgo_id == hallazgo.id
                )
            )
            .all()
        )
        assert len(historial) == 1
        assert historial[0].estado_anterior is None
        assert historial[0].estado_nuevo == "caries"
    finally:
        session.close()


def test_upsert_segunda_version_historial_con_anterior_nuevo():
    session = _session()
    try:
        paciente = _crear_paciente(session)
        autor = _usuario_odontologo(session)
        servicio = OdontogramaService(session)
        servicio.obtener_o_crear(paciente.id)
        # Primera versión
        servicio.upsert(
            paciente_id=paciente.id,
            pieza=13,
            datos=HallazgoIn(estado="sano", observacion="Inicial"),
            usuario=autor,
        )
        # Segunda versión (cambio de estado)
        h2 = servicio.upsert(
            paciente_id=paciente.id,
            pieza=13,
            datos=HallazgoIn(estado="caries", observacion="Nueva"),
            usuario=autor,
        )
        # Verificar historial: debe haber 2 filas, la más reciente primero
        historial = (
            session.scalars(
                __import__("sqlalchemy").select(HallazgoPiezaHistorial)
                .where(HallazgoPiezaHistorial.hallazgo_id == h2.id)
                .order_by(HallazgoPiezaHistorial.registrado_en.desc())
            )
            .all()
        )
        assert len(historial) == 2
        # La versión más reciente debe tener estado_anterior='sano' y estado_nuevo='caries'
        ultima = historial[0]
        assert ultima.estado_anterior == "sano"
        assert ultima.estado_nuevo == "caries"
        # La primera versión debe tener estado_anterior=NULL y estado_nuevo='sano'
        primera = historial[1]
        assert primera.estado_anterior is None
        assert primera.estado_nuevo == "sano"
    finally:
        session.close()


def test_no_loguea_datos_clinicos_evolucion(caplog):
    """R9: no se loguea texto ni estado de evolución."""
    caplog.set_level(logging.DEBUG)
    session = _session()
    try:
        paciente = _crear_paciente(session)
        autor = _usuario_odontologo(session)
        servicio = EvolucionService(session)
        servicio.crear(
            paciente_id=paciente.id,
            texto="Dato clínico confidencial que no debe loguearse",
            autor_usuario_id=autor.id,
        )
        propios = [
            registro.getMessage()
            for registro in caplog.records
            if registro.name.startswith("app")
        ]
        assert all("Dato clínico confidencial" not in m for m in propios)
        assert all("sensibilidad" not in m.lower() for m in propios)
    finally:
        session.close()


def test_no_loguea_datos_clinicos_consentimiento(caplog):
    """R9: no se loguea versión de consentimiento."""
    caplog.set_level(logging.DEBUG)
    session = _session()
    try:
        paciente = _crear_paciente(session)
        autor = _usuario_odontologo(session)
        servicio = ConsentimientoService(session)
        servicio.crear(
            paciente_id=paciente.id,
            version="v-confidencial",
            autor_usuario_id=autor.id,
        )
        propios = [
            registro.getMessage()
            for registro in caplog.records
            if registro.name.startswith("app")
        ]
        assert all("v-confidencial" not in m for m in propios)
    finally:
        session.close()


def test_no_loguea_estado_ni_observacion_upsert(caplog):
    """R9: no se loguea estado ni observación del upsert de pieza."""
    caplog.set_level(logging.DEBUG)
    session = _session()
    try:
        paciente = _crear_paciente(session)
        autor = _usuario_odontologo(session)
        servicio = OdontogramaService(session)
        servicio.obtener_o_crear(paciente.id)
        servicio.upsert(
            paciente_id=paciente.id,
            pieza=11,
            datos=HallazgoIn(estado="caries", observacion="Observación clínica confidencial"),
            usuario=autor,
        )
        propios = [
            registro.getMessage()
            for registro in caplog.records
            if registro.name.startswith("app")
        ]
        assert all("caries" not in m for m in propios)
        assert all("Observación clínica confidencial" not in m for m in propios)
    finally:
        session.close()
