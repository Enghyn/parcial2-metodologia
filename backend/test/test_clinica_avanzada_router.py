"""Tests de router de ficha clínica avanzada (C-11, TDD).

RED: estos tests deben fallar porque los endpoints de evolución y
consentimiento no existen aún.
"""
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.core.security import crear_access_token
from app.db.session import get_session_factory
from app.main import create_app
from app.modules.admin.models import Usuario
from app.modules.clinica.models import Paciente
from app.modules.clinica.schemas import HallazgoIn
from app.modules.clinica.service import OdontogramaService
from sqlalchemy import select

pytestmark = [pytest.mark.integration]

BASE = "/api/v1/pacientes"


def app_fresco():
    return create_app()


def _session():
    return get_session_factory()()


def _crear_paciente(session, dni: str | None = None) -> Paciente:
    if dni is None:
        dni = uuid4().hex[:12]
    p = Paciente(nombre="Paciente Router", dni=dni, telefono="1122334455", activo=True)
    session.add(p)
    session.commit()
    session.refresh(p)
    return p


def _token_para(usuario: Usuario) -> str:
    return crear_access_token(
        sub=str(usuario.id),
        rol=usuario.rol,
        secret=get_settings().jwt_secret,
        expire_min=30,
    )


def _usuario_odontologo(session) -> Usuario:
    u = session.scalar(
        select(Usuario).where(Usuario.rol == "odontologo", Usuario.activo.is_(True))
    )
    if u is None:
        raise RuntimeError("No hay odontólogo activo en la base de pruebas")
    return u


def _odontologo_token(session) -> str:
    u = session.scalar(
        __import__("sqlalchemy").select(Usuario).where(
            Usuario.rol == "odontologo", Usuario.activo.is_(True)
        )
    )
    return _token_para(u)


def _recepcion_token(session) -> str:
    u = session.scalar(
        __import__("sqlalchemy").select(Usuario).where(
            Usuario.rol == "recepcion", Usuario.activo.is_(True)
        )
    )
    return _token_para(u)


@pytest.mark.asyncio
async def test_post_evolucion_odontologo_201():
    session = _session()
    try:
        paciente = _crear_paciente(session)
        token = _odontologo_token(session)
        app = app_fresco()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(
                f"{BASE}/{paciente.id}/evoluciones",
                json={"texto": "Evolución de prueba"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 201, r.text
        cuerpo = r.json()
        assert cuerpo["texto"] == "Evolución de prueba"
        assert cuerpo["paciente_id"] == str(paciente.id)
        # Limpieza del paciente
        p = session.get(Paciente, paciente.id)
        if p is not None:
            p.soft_delete()
            session.commit()
    finally:
        session.close()


@pytest.mark.asyncio
async def test_post_evolucion_recepcion_403():
    session = _session()
    try:
        paciente = _crear_paciente(session)
        token = _recepcion_token(session)
        app = app_fresco()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(
                f"{BASE}/{paciente.id}/evoluciones",
                json={"texto": "Evolución de prueba"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 403, r.text
        p = session.get(Paciente, paciente.id)
        if p is not None:
            p.soft_delete()
            session.commit()
    finally:
        session.close()


@pytest.mark.asyncio
async def test_post_evolucion_sin_token_401():
    session = _session()
    try:
        paciente = _crear_paciente(session)
        app = app_fresco()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(
                f"{BASE}/{paciente.id}/evoluciones",
                json={"texto": "Evolución de prueba"},
            )
        assert r.status_code == 401, r.text
        p = session.get(Paciente, paciente.id)
        if p is not None:
            p.soft_delete()
            session.commit()
    finally:
        session.close()


@pytest.mark.asyncio
async def test_get_evoluciones_tres_roles_200():
    session = _session()
    try:
        paciente = _crear_paciente(session)
        # Crear una evolución directamente en la BD para tener algo que leer
        from app.core.timezone import ahora
        from app.modules.clinica.models import EvolucionClinica

        autor = session.scalar(
            __import__("sqlalchemy").select(Usuario).where(
                Usuario.rol == "odontologo", Usuario.activo.is_(True)
            )
        )
        evo = EvolucionClinica(
            paciente_id=paciente.id,
            autor_usuario_id=autor.id,
            texto="Evolución previa",
            fecha=ahora(),
        )
        session.add(evo)
        session.commit()

        app = app_fresco()
        for rol in ("odontologo", "recepcion", "admin"):
            u = session.scalar(
                __import__("sqlalchemy").select(Usuario).where(
                    Usuario.rol == rol, Usuario.activo.is_(True)
                )
            )
            token = _token_para(u)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                r = await client.get(
                    f"{BASE}/{paciente.id}/evoluciones",
                    headers={"Authorization": f"Bearer {token}"},
                )
            assert r.status_code == 200, f"{rol}: {r.text}"
            cuerpo = r.json()
            assert isinstance(cuerpo, list)
            assert len(cuerpo) >= 1

        p = session.get(Paciente, paciente.id)
        if p is not None:
            p.soft_delete()
            session.commit()
    finally:
        session.close()


@pytest.mark.asyncio
async def test_post_consentimiento_odontologo_201():
    session = _session()
    try:
        paciente = _crear_paciente(session)
        token = _odontologo_token(session)
        app = app_fresco()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(
                f"{BASE}/{paciente.id}/consentimientos",
                json={"version": "v1"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 201, r.text
        cuerpo = r.json()
        assert cuerpo["version"] == "v1"
        assert cuerpo["paciente_id"] == str(paciente.id)
        p = session.get(Paciente, paciente.id)
        if p is not None:
            p.soft_delete()
            session.commit()
    finally:
        session.close()


@pytest.mark.asyncio
async def test_post_consentimiento_recepcion_403():
    session = _session()
    try:
        paciente = _crear_paciente(session)
        token = _recepcion_token(session)
        app = app_fresco()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(
                f"{BASE}/{paciente.id}/consentimientos",
                json={"version": "v1"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 403, r.text
        p = session.get(Paciente, paciente.id)
        if p is not None:
            p.soft_delete()
            session.commit()
    finally:
        session.close()


@pytest.mark.asyncio
async def test_get_consentimientos_tres_roles_200():
    session = _session()
    try:
        paciente = _crear_paciente(session)
        from app.core.timezone import ahora
        from app.modules.clinica.models import ConsentimientoInformado

        autor = session.scalar(
            __import__("sqlalchemy").select(Usuario).where(
                Usuario.rol == "odontologo", Usuario.activo.is_(True)
            )
        )
        cons = ConsentimientoInformado(
            paciente_id=paciente.id,
            version="v1",
            autor_usuario_id=autor.id,
            fecha=ahora(),
        )
        session.add(cons)
        session.commit()

        app = app_fresco()
        for rol in ("odontologo", "recepcion", "admin"):
            u = session.scalar(
                __import__("sqlalchemy").select(Usuario).where(
                    Usuario.rol == rol, Usuario.activo.is_(True)
                )
            )
            token = _token_para(u)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                r = await client.get(
                    f"{BASE}/{paciente.id}/consentimientos",
                    headers={"Authorization": f"Bearer {token}"},
                )
            assert r.status_code == 200, f"{rol}: {r.text}"
            cuerpo = r.json()
            assert isinstance(cuerpo, list)
            assert len(cuerpo) >= 1

        p = session.get(Paciente, paciente.id)
        if p is not None:
            p.soft_delete()
            session.commit()
    finally:
        session.close()


@pytest.mark.asyncio
async def test_get_historial_pieza_tres_roles_200():
    session = _session()
    try:
        paciente = _crear_paciente(session)
        autor = _usuario_odontologo(session)
        servicio = OdontogramaService(session)
        servicio.upsert(
            paciente_id=paciente.id,
            pieza=12,
            datos=HallazgoIn(estado="caries", observacion="Primera versión"),
            usuario=autor,
        )
        app = app_fresco()
        for rol in ("odontologo", "recepcion", "admin"):
            u = session.scalar(
                __import__("sqlalchemy").select(Usuario).where(
                    Usuario.rol == rol, Usuario.activo.is_(True)
                )
            )
            token = _token_para(u)
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                r = await client.get(
                    f"{BASE}/{paciente.id}/odontograma/piezas/12/historial",
                    headers={"Authorization": f"Bearer {token}"},
                )
            assert r.status_code == 200, f"{rol}: {r.text}"
            cuerpo = r.json()
            assert isinstance(cuerpo, list)
            assert len(cuerpo) >= 1
            assert cuerpo[0]["estado_nuevo"] == "caries"

        p = session.get(Paciente, paciente.id)
        if p is not None:
            p.soft_delete()
            session.commit()
    finally:
        session.close()


@pytest.mark.asyncio
async def test_get_historial_pieza_pieza_invalida_422():
    session = _session()
    try:
        paciente = _crear_paciente(session)
        autor = _usuario_odontologo(session)
        token = _token_para(autor)
        app = app_fresco()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get(
                f"{BASE}/{paciente.id}/odontograma/piezas/19/historial",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 422, r.text

        p = session.get(Paciente, paciente.id)
        if p is not None:
            p.soft_delete()
            session.commit()
    finally:
        session.close()


@pytest.mark.asyncio
async def test_get_historial_pieza_sin_hallazgos_200_lista_vacia():
    session = _session()
    try:
        paciente = _crear_paciente(session)
        autor = _usuario_odontologo(session)
        token = _token_para(autor)
        app = app_fresco()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get(
                f"{BASE}/{paciente.id}/odontograma/piezas/11/historial",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 200, r.text
        cuerpo = r.json()
        assert isinstance(cuerpo, list)
        assert len(cuerpo) == 0

        p = session.get(Paciente, paciente.id)
        if p is not None:
            p.soft_delete()
            session.commit()
    finally:
        session.close()


@pytest.mark.asyncio
async def test_get_historial_pieza_paciente_borrado_404():
    session = _session()
    try:
        paciente = _crear_paciente(session)
        autor = _usuario_odontologo(session)
        token = _token_para(autor)
        paciente.soft_delete()
        session.commit()
        app = app_fresco()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get(
                f"{BASE}/{paciente.id}/odontograma/piezas/11/historial",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert r.status_code == 404, r.text
    finally:
        session.close()
