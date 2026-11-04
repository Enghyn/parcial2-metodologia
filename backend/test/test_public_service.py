"""TDD C-06 grupos 2-4 — PublicReservaService contra Postgres (integración).

Requiere base migrada + seeded (alembic upgrade head + python -m app.db.seed).
"""
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_session_factory
from app.modules.agenda.models import Bloqueo, Profesional, Sillon, Turno
from app.modules.agenda.schemas import BloqueoCreate, TurnoCreate
from app.modules.agenda.service import TurnoService
from app.modules.clinica.models import Paciente
from app.modules.public.schemas import PacientePublicoIn, ReservaCreate
from app.modules.public.service import PublicReservaService


def _session() -> Session:
    return get_session_factory()()


def _seed_ids(session: Session) -> dict:
    sillones = list(
        session.scalars(
            select(Sillon).where(Sillon.deleted_at.is_(None)).order_by(Sillon.nombre)
        )
    )
    profesionales = list(
        session.scalars(
            select(Profesional)
            .where(Profesional.deleted_at.is_(None), Profesional.activo.is_(True))
            .order_by(Profesional.matricula)
        )
    )
    pacientes = list(session.scalars(select(Paciente).where(Paciente.deleted_at.is_(None))))
    return {
        "sillones": sillones,
        "profesionales": profesionales,
        "paciente": pacientes[0],
    }


def _dni_unico() -> str:
    return "P" + uuid4().hex[:12]


def _reserva(
    *,
    sillon_id,
    profesional_id,
    inicio: datetime,
    dni: str | None = None,
    duracion: int = 30,
    nombre: str = "Paciente Público",
) -> ReservaCreate:
    return ReservaCreate(
        prestacion="Consulta",
        duracion_min=duracion,
        inicio=inicio,
        profesional_id=profesional_id,
        sillon_id=sillon_id,
        paciente=PacientePublicoIn(
            nombre=nombre,
            dni=dni or _dni_unico(),
            telefono="1144556677",
        ),
    )


def _uuid_set(items) -> set:
    return {i.id for i in items}


def test_disponibilidad_devuelve_slots_ordenados() -> None:
    session = _session()
    try:
        ids = _seed_ids(session)
        servicio = PublicReservaService(session)
        slots = servicio.disponibilidad(date(2027, 9, 1), 30)
        assert slots != []
        assert slots[0].inicio.hour == 8
        assert slots[0].inicio.minute == 0
        assert {s.profesional_id for s in slots} <= _uuid_set(ids["profesionales"])
        assert {s.sillon_id for s in slots} <= _uuid_set(ids["sillones"])
        inicios = [s.inicio for s in slots]
        assert inicios == sorted(inicios)
    finally:
        session.close()


def test_disponibilidad_sin_capacidad() -> None:
    session = _session()
    try:
        ids = _seed_ids(session)
        servicio = PublicReservaService(session)
        day_start = datetime(2027, 9, 2, 0, 0, tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)
        agenda = TurnoService(session)
        bloqueos = [
            agenda.crear_bloqueo(
                BloqueoCreate(
                    profesional_id=prof.id,
                    desde=day_start,
                    hasta=day_end,
                    motivo="Test sin capacidad",
                )
            )
            for prof in ids["profesionales"]
        ]
        try:
            assert servicio.disponibilidad(date(2027, 9, 2), 30) == []
        finally:
            for bloqueo in bloqueos:
                TurnoService(session).eliminar_bloqueo(bloqueo.id)
    finally:
        session.close()


def test_disponibilidad_excluye_bloqueo_de_sillon() -> None:
    session = _session()
    try:
        ids = _seed_ids(session)
        sillon = ids["sillones"][0]
        inicio = datetime(2027, 9, 3, 9, 0, tzinfo=timezone.utc)
        fin = inicio + timedelta(minutes=30)
        servicio = PublicReservaService(session)
        bloqueo = TurnoService(session).crear_bloqueo(
            BloqueoCreate(sillon_id=sillon.id, desde=inicio, hasta=fin, motivo="Test bloqueo")
        )
        try:
            slots = servicio.disponibilidad(date(2027, 9, 3), 30)
            en_rango = [s for s in slots if s.inicio == inicio]
            assert en_rango != []
            assert all(s.sillon_id != sillon.id for s in en_rango)
        finally:
            TurnoService(session).eliminar_bloqueo(bloqueo.id)
    finally:
        session.close()


def test_turno_cancelado_libera_slot() -> None:
    session = _session()
    try:
        ids = _seed_ids(session)
        sillon = ids["sillones"][0]
        prof = ids["profesionales"][0]
        paciente = ids["paciente"]
        inicio = datetime(2027, 9, 4, 9, 0, tzinfo=timezone.utc)
        agenda = TurnoService(session)
        turno = agenda.crear(
            TurnoCreate(
                paciente_id=paciente.id,
                profesional_id=prof.id,
                sillon_id=sillon.id,
                prestacion="Consulta",
                inicio=inicio,
                duracion_min=30,
            )
        )
        try:
            agenda.cambiar_estado(turno.id, "cancelado")
            slots = PublicReservaService(session).disponibilidad(date(2027, 9, 4), 30)
            assert any(s.inicio == inicio and s.profesional_id == prof.id for s in slots)
        finally:
            turno.soft_delete()
            session.commit()
    finally:
        session.close()


def test_find_or_create_paciente_reutiliza_por_dni() -> None:
    session = _session()
    try:
        ids = _seed_ids(session)
        sillon = ids["sillones"][0]
        prof = ids["profesionales"][0]
        dni = _dni_unico()
        servicio = PublicReservaService(session)
        t1 = servicio.reservar(
            _reserva(
                sillon_id=sillon.id,
                profesional_id=prof.id,
                inicio=datetime(2027, 9, 5, 9, 0, tzinfo=timezone.utc),
                dni=dni,
            )
        )
        t2 = servicio.reservar(
            _reserva(
                sillon_id=sillon.id,
                profesional_id=prof.id,
                inicio=datetime(2027, 9, 5, 10, 0, tzinfo=timezone.utc),
                dni=dni,
            )
        )
        try:
            paciente = session.scalar(select(Paciente).where(Paciente.dni == dni))
            assert paciente is not None
            cantidad = session.scalar(
                select(func.count()).select_from(Paciente).where(Paciente.dni == dni)
            )
            assert cantidad == 1
            assert t1.paciente_id == paciente.id
            assert t2.paciente_id == paciente.id
        finally:
            t1.soft_delete()
            t2.soft_delete()
            paciente = session.scalar(select(Paciente).where(Paciente.dni == dni))
            if paciente is not None:
                paciente.soft_delete()
            session.commit()
    finally:
        session.close()


def test_reserva_crea_turno_reservado_con_token() -> None:
    session = _session()
    try:
        ids = _seed_ids(session)
        sillon = ids["sillones"][0]
        prof = ids["profesionales"][0]
        dni = _dni_unico()
        inicio = datetime(2027, 9, 6, 9, 0, tzinfo=timezone.utc)
        turno = PublicReservaService(session).reservar(
            _reserva(sillon_id=sillon.id, profesional_id=prof.id, inicio=inicio, dni=dni)
        )
        try:
            assert turno.estado == "reservado"
            assert turno.token_publico is not None
            assert turno.fin == inicio + timedelta(minutes=30)
        finally:
            turno.soft_delete()
            paciente = session.scalar(select(Paciente).where(Paciente.dni == dni))
            if paciente is not None:
                paciente.soft_delete()
            session.commit()
    finally:
        session.close()


def test_reserva_en_hueco_ocupado_409() -> None:
    session = _session()
    try:
        ids = _seed_ids(session)
        sillon = ids["sillones"][0]
        prof = ids["profesionales"][0]
        inicio = datetime(2027, 9, 7, 9, 0, tzinfo=timezone.utc)
        servicio = PublicReservaService(session)
        dni_ok = _dni_unico()
        dni_conflicto = _dni_unico()
        turno = servicio.reservar(
            _reserva(sillon_id=sillon.id, profesional_id=prof.id, inicio=inicio, dni=dni_ok)
        )
        token = turno.token_publico
        with pytest.raises(HTTPException) as exc:
            servicio.reservar(
                _reserva(
                    sillon_id=sillon.id,
                    profesional_id=prof.id,
                    inicio=inicio,
                    dni=dni_conflicto,
                )
            )
        assert exc.value.status_code == 409
        session.rollback()
        turno = session.scalar(select(Turno).where(Turno.token_publico == token))
        if turno is not None:
            turno.soft_delete()
        for dni in (dni_ok, dni_conflicto):
            paciente = session.scalar(select(Paciente).where(Paciente.dni == dni))
            if paciente is not None:
                paciente.soft_delete()
        session.commit()
    finally:
        session.close()


def test_obtener_por_token_ok_y_404() -> None:
    session = _session()
    try:
        ids = _seed_ids(session)
        sillon = ids["sillones"][0]
        prof = ids["profesionales"][0]
        dni = _dni_unico()
        servicio = PublicReservaService(session)
        turno = servicio.reservar(
            _reserva(
                sillon_id=sillon.id,
                profesional_id=prof.id,
                inicio=datetime(2027, 9, 8, 9, 0, tzinfo=timezone.utc),
                dni=dni,
            )
        )
        try:
            encontrado = servicio.obtener_por_token(turno.token_publico)
            assert encontrado.id == turno.id
            with pytest.raises(HTTPException) as exc:
                servicio.obtener_por_token(uuid4())
            assert exc.value.status_code == 404
            assert "Turno no encontrado" in str(exc.value.detail)
        finally:
            turno.soft_delete()
            paciente = session.scalar(select(Paciente).where(Paciente.dni == dni))
            if paciente is not None:
                paciente.soft_delete()
            session.commit()
    finally:
        session.close()


def test_cancelar_por_token_ok_y_409() -> None:
    session = _session()
    try:
        ids = _seed_ids(session)
        sillon = ids["sillones"][0]
        prof = ids["profesionales"][0]
        dni = _dni_unico()
        servicio = PublicReservaService(session)
        turno = servicio.reservar(
            _reserva(
                sillon_id=sillon.id,
                profesional_id=prof.id,
                inicio=datetime(2027, 9, 9, 9, 0, tzinfo=timezone.utc),
                dni=dni,
            )
        )
        try:
            cancelado = servicio.cancelar_por_token(turno.token_publico)
            assert cancelado.estado == "cancelado"
            with pytest.raises(HTTPException) as exc:
                servicio.cancelar_por_token(turno.token_publico)
            assert exc.value.status_code == 409
            with pytest.raises(HTTPException) as exc2:
                servicio.cancelar_por_token(uuid4())
            assert exc2.value.status_code == 404
        finally:
            turno.soft_delete()
            paciente = session.scalar(select(Paciente).where(Paciente.dni == dni))
            if paciente is not None:
                paciente.soft_delete()
            session.commit()
    finally:
        session.close()


def test_cancelar_turno_atendido_409() -> None:
    session = _session()
    try:
        ids = _seed_ids(session)
        sillon = ids["sillones"][0]
        prof = ids["profesionales"][0]
        dni = _dni_unico()
        servicio = PublicReservaService(session)
        turno = servicio.reservar(
            _reserva(
                sillon_id=sillon.id,
                profesional_id=prof.id,
                inicio=datetime(2027, 9, 10, 9, 0, tzinfo=timezone.utc),
                dni=dni,
            )
        )
        try:
            TurnoService(session).cambiar_estado(turno.id, "atendido")
            with pytest.raises(HTTPException) as exc:
                servicio.cancelar_por_token(turno.token_publico)
            assert exc.value.status_code == 409
            assert "atendido" in str(exc.value.detail)
        finally:
            turno.soft_delete()
            paciente = session.scalar(select(Paciente).where(Paciente.dni == dni))
            if paciente is not None:
                paciente.soft_delete()
            session.commit()
    finally:
        session.close()


def test_to_public_no_expone_datos_sensibles() -> None:
    session = _session()
    try:
        ids = _seed_ids(session)
        sillon = ids["sillones"][0]
        prof = ids["profesionales"][0]
        dni = _dni_unico()
        servicio = PublicReservaService(session)
        turno = servicio.reservar(
            _reserva(
                sillon_id=sillon.id,
                profesional_id=prof.id,
                inicio=datetime(2027, 9, 11, 9, 0, tzinfo=timezone.utc),
                dni=dni,
            )
        )
        try:
            publico = servicio.to_public(turno)
            assert publico.paciente_nombre == "Paciente Público"
            assert publico.profesional_nombre == prof.nombre
            assert publico.sillon_nombre == sillon.nombre
            assert not hasattr(publico, "dni")
            assert not hasattr(publico, "telefono")
        finally:
            turno.soft_delete()
            paciente = session.scalar(select(Paciente).where(Paciente.dni == dni))
            if paciente is not None:
                paciente.soft_delete()
            session.commit()
    finally:
        session.close()
