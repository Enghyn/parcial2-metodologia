"""TDD C-04 grupo 4 — TurnoService contra Postgres (integración).

Requiere base migrada + seeded (alembic upgrade head + python -m app.db.seed).
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_session_factory
from app.modules.agenda.models import Bloqueo, Profesional, Sillon, Turno
from app.modules.clinica.models import Paciente
from app.modules.agenda.schemas import BloqueoCreate, TurnoCreate
from app.modules.agenda.service import TurnoService


def _session() -> Session:
    return get_session_factory()()


def _seed_ids(session: Session) -> dict:
    sillones = list(session.scalars(select(Sillon).where(Sillon.deleted_at.is_(None)).order_by(Sillon.nombre)))
    profesionales = list(session.scalars(select(Profesional).where(Profesional.deleted_at.is_(None)).order_by(Profesional.matricula)))
    pacientes = list(session.scalars(select(Paciente).where(Paciente.deleted_at.is_(None))))
    return {
        "sillones": sillones,
        "profesionales": profesionales,
        "paciente": pacientes[0],
    }


def _base_turno(sillon_id, profesional_id, paciente_id, inicio, duracion=30) -> TurnoCreate:
    return TurnoCreate(
        paciente_id=paciente_id,
        profesional_id=profesional_id,
        sillon_id=sillon_id,
        prestacion="Consulta",
        inicio=inicio,
        duracion_min=duracion,
    )


def test_crear_en_hueco_libre_persiste_fin() -> None:
    session = _session()
    try:
        ids = _seed_ids(session)
        sillon = ids["sillones"][0]
        prof = ids["profesionales"][0]
        paciente = ids["paciente"]
        inicio = datetime(2026, 12, 1, 9, 0, tzinfo=timezone.utc)
        servicio = TurnoService(session)
        turno = servicio.crear(_base_turno(sillon.id, prof.id, paciente.id, inicio, 30))
        session.commit()
        assert turno.fin == inicio + timedelta(minutes=30)
        # cleanup
        turno.soft_delete()
        session.commit()
    finally:
        session.close()


def test_conflicto_mismo_sillon_409() -> None:
    session = _session()
    try:
        ids = _seed_ids(session)
        sillon = ids["sillones"][0]
        prof_a = ids["profesionales"][0]
        prof_b = ids["profesionales"][1]
        paciente = ids["paciente"]
        inicio = datetime(2026, 12, 2, 9, 0, tzinfo=timezone.utc)
        servicio = TurnoService(session)
        t1 = servicio.crear(_base_turno(sillon.id, prof_a.id, paciente.id, inicio, 30))
        session.commit()
        with pytest.raises(HTTPException) as exc:
            servicio.crear(_base_turno(sillon.id, prof_b.id, paciente.id, inicio, 30))
        assert exc.value.status_code == 409
        assert "sillón" in str(exc.value.detail)
        t1.soft_delete()
        session.commit()
    finally:
        session.close()


def test_conflicto_mismo_profesional_distinto_sillon_409() -> None:
    session = _session()
    try:
        ids = _seed_ids(session)
        sillon_a = ids["sillones"][0]
        sillon_b = ids["sillones"][1]
        prof = ids["profesionales"][0]
        paciente = ids["paciente"]
        inicio = datetime(2026, 12, 3, 9, 0, tzinfo=timezone.utc)
        servicio = TurnoService(session)
        t1 = servicio.crear(_base_turno(sillon_a.id, prof.id, paciente.id, inicio, 30))
        session.commit()
        with pytest.raises(HTTPException) as exc:
            servicio.crear(_base_turno(sillon_b.id, prof.id, paciente.id, inicio, 30))
        assert exc.value.status_code == 409
        assert "profesional" in str(exc.value.detail)
        t1.soft_delete()
        session.commit()
    finally:
        session.close()


def test_mismo_horario_distinto_recurso_ok() -> None:
    session = _session()
    try:
        ids = _seed_ids(session)
        sillon_a = ids["sillones"][0]
        sillon_b = ids["sillones"][1]
        prof_a = ids["profesionales"][0]
        prof_b = ids["profesionales"][1]
        paciente = ids["paciente"]
        inicio = datetime(2026, 12, 4, 9, 0, tzinfo=timezone.utc)
        servicio = TurnoService(session)
        t1 = servicio.crear(_base_turno(sillon_a.id, prof_a.id, paciente.id, inicio, 30))
        t2 = servicio.crear(_base_turno(sillon_b.id, prof_b.id, paciente.id, inicio, 30))
        session.commit()
        assert t1.id != t2.id
        t1.soft_delete()
        t2.soft_delete()
        session.commit()
    finally:
        session.close()


def test_creacion_sobre_turno_cancelado_ok() -> None:
    session = _session()
    try:
        ids = _seed_ids(session)
        sillon = ids["sillones"][0]
        prof = ids["profesionales"][0]
        paciente = ids["paciente"]
        inicio = datetime(2026, 12, 5, 9, 0, tzinfo=timezone.utc)
        servicio = TurnoService(session)
        t1 = servicio.crear(_base_turno(sillon.id, prof.id, paciente.id, inicio, 30))
        session.commit()
        servicio.cambiar_estado(t1.id, "cancelado")
        session.commit()
        t2 = servicio.crear(_base_turno(sillon.id, prof.id, paciente.id, inicio, 30))
        session.commit()
        assert t2.id != t1.id
        t1.soft_delete()
        t2.soft_delete()
        session.commit()
    finally:
        session.close()


def test_listar_filtros_y_excluye_borrados() -> None:
    session = _session()
    try:
        ids = _seed_ids(session)
        sillon = ids["sillones"][0]
        prof = ids["profesionales"][0]
        paciente = ids["paciente"]
        inicio = datetime(2026, 12, 6, 9, 0, tzinfo=timezone.utc)
        servicio = TurnoService(session)
        t1 = servicio.crear(_base_turno(sillon.id, prof.id, paciente.id, inicio, 30))
        session.commit()
        # listar por fecha
        fecha = inicio.date()
        todos = servicio.listar(fecha=fecha, profesional_id=prof.id, sillon_id=sillon.id)
        assert any(t.id == t1.id for t in todos)
        # soft delete → excluded
        t1.soft_delete()
        session.commit()
        despues = servicio.listar(fecha=fecha, profesional_id=prof.id, sillon_id=sillon.id)
        assert all(t.id != t1.id for t in despues)
    finally:
        session.close()


def test_cambiar_estado_inexistente_404() -> None:
    session = _session()
    try:
        servicio = TurnoService(session)
        from uuid import uuid4

        with pytest.raises(HTTPException) as exc:
            servicio.cambiar_estado(uuid4(), "confirmado")
        assert exc.value.status_code == 404
        assert "Turno no encontrado" in str(exc.value.detail)
    finally:
        session.close()


def test_crear_y_eliminar_bloqueo() -> None:
    session = _session()
    try:
        ids = _seed_ids(session)
        sillon = ids["sillones"][0]
        inicio = datetime(2026, 12, 7, 9, 0, tzinfo=timezone.utc)
        fin = inicio + timedelta(minutes=60)
        servicio = TurnoService(session)
        bloqueo = servicio.crear_bloqueo(
            BloqueoCreate(sillon_id=sillon.id, desde=inicio, hasta=fin, motivo="Limpieza")
        )
        session.commit()
        assert bloqueo.id is not None
        servicio.eliminar_bloqueo(bloqueo.id)
        session.commit()
        # ya no existe
        with pytest.raises(HTTPException) as exc:
            servicio.eliminar_bloqueo(bloqueo.id)
        assert exc.value.status_code == 404
    finally:
        session.close()


def test_bloqueo_conflicto_en_turno() -> None:
    session = _session()
    try:
        ids = _seed_ids(session)
        sillon = ids["sillones"][0]
        prof = ids["profesionales"][0]
        paciente = ids["paciente"]
        inicio = datetime(2026, 12, 8, 9, 0, tzinfo=timezone.utc)
        servicio = TurnoService(session)
        # bloqueo primero
        bloqueo = servicio.crear_bloqueo(
            BloqueoCreate(sillon_id=sillon.id, desde=inicio, hasta=inicio + timedelta(minutes=30), motivo="X")
        )
        session.commit()
        with pytest.raises(HTTPException) as exc:
            servicio.crear(_base_turno(sillon.id, prof.id, paciente.id, inicio, 30))
        assert exc.value.status_code == 409
        assert "bloqueado" in str(exc.value.detail)
        servicio.eliminar_bloqueo(bloqueo.id)
        session.commit()
    finally:
        session.close()