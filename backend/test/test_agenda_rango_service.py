"""TDD C-09b grupo 3 — `TurnoService.listar` por rango de días ART (integración).

Requiere base migrada + seeded (`alembic upgrade head` + `python -m app.db.seed`).
Semana de prueba: lunes 2027-02-01 a domingo 2027-02-07 (ART).

3.1: límites inclusivos, domingo anterior excluido, borrado lógico excluido,
`cancelado` incluido, filtros de recurso combinados y orden determinista.
"""
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.timezone import TZ_CONSULTORIO, inicio_dia
from app.db import registry  # noqa: F401  (registra usuarios/turnos para las FKs)
from app.db.session import get_session_factory
from app.modules.admin.models import Usuario
from app.modules.agenda.models import Profesional, Sillon, Turno
from app.modules.agenda.schemas import SobreturnoCreate, TurnoCreate
from app.modules.agenda.service import TurnoService
from app.modules.clinica.models import Paciente

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("db_disponible")]

LUNES = date(2028, 1, 3)
DOMINGO = date(2028, 1, 9)

# Ventana que limpia el fixture: incluye el domingo anterior y el rango de 31 días.
_LIMPIEZA_DESDE = datetime(2027, 12, 20, tzinfo=UTC)
_LIMPIEZA_HASTA = datetime(2028, 2, 20, tzinfo=UTC)


def _limpiar_datos_de_prueba() -> None:
    session = get_session_factory()()
    try:
        turnos = list(
            session.scalars(
                select(Turno).where(
                    Turno.inicio >= _LIMPIEZA_DESDE,
                    Turno.inicio < _LIMPIEZA_HASTA,
                    Turno.deleted_at.is_(None),
                )
            )
        )
        for turno in turnos:
            turno.soft_delete()
        session.commit()
    finally:
        session.close()


@pytest.fixture(autouse=True)
def _base_limpia() -> Iterator[None]:
    _limpiar_datos_de_prueba()
    yield
    _limpiar_datos_de_prueba()


@pytest.fixture
def session() -> Iterator[Session]:
    sesion = get_session_factory()()
    try:
        yield sesion
    finally:
        sesion.close()


def _seed_ids(session: Session) -> dict[str, Any]:
    sillones = list(
        session.scalars(
            select(Sillon)
            .where(Sillon.deleted_at.is_(None), Sillon.activo.is_(True))
            .order_by(Sillon.nombre)
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
        "sillon_a": sillones[0],
        "sillon_b": sillones[1],
        "prof_a": profesionales[0],
        "prof_b": profesionales[1],
        "paciente": pacientes[0],
    }


def _turno(
    session: Session,
    ids: dict[str, Any],
    cuando: datetime,
    *,
    sillon: str = "sillon_a",
    profesional: str = "prof_a",
    duracion: int = 30,
) -> Turno:
    datos = TurnoCreate(
        paciente_id=ids["paciente"].id,
        profesional_id=ids[profesional].id,
        sillon_id=ids[sillon].id,
        prestacion="Consulta",
        inicio=cuando,
        duracion_min=duracion,
    )
    turno = TurnoService(session).crear(datos)
    session.commit()
    return turno


def _ids(turnos: list[Turno]) -> set[UUID]:
    return {turno.id for turno in turnos}


def test_rango_incluye_lunes_00_y_domingo_2330(session: Session) -> None:
    ids = _seed_ids(session)
    servicio = TurnoService(session)
    lunes_medianoche = _turno(
        session,
        ids,
        datetime.combine(LUNES, datetime.min.time(), tzinfo=TZ_CONSULTORIO),
    )
    domingo_noche = _turno(
        session,
        ids,
        datetime(2028, 1, 9, 23, 30, tzinfo=TZ_CONSULTORIO),
    )

    resultado = servicio.listar(desde=LUNES, hasta=DOMINGO)

    assert _ids(resultado) >= {lunes_medianoche.id, domingo_noche.id}


def test_rango_excluye_domingo_anterior_2330(session: Session) -> None:
    ids = _seed_ids(session)
    servicio = TurnoService(session)
    domingo_anterior = _turno(
        session,
        ids,
        datetime(2028, 1, 2, 23, 30, tzinfo=TZ_CONSULTORIO),
    )

    resultado = servicio.listar(desde=LUNES, hasta=DOMINGO)

    assert domingo_anterior.id not in _ids(resultado)
    assert all(turno.inicio >= inicio_dia(LUNES) for turno in resultado)


def test_rango_excluye_turno_borrado_logicamente(session: Session) -> None:
    ids = _seed_ids(session)
    servicio = TurnoService(session)
    turno = _turno(session, ids, datetime(2028, 1, 4, 9, 0, tzinfo=TZ_CONSULTORIO))
    assert turno.id in _ids(servicio.listar(desde=LUNES, hasta=DOMINGO))

    turno.soft_delete()
    session.commit()

    assert turno.id not in _ids(servicio.listar(desde=LUNES, hasta=DOMINGO))


def test_rango_incluye_turno_cancelado(session: Session) -> None:
    ids = _seed_ids(session)
    servicio = TurnoService(session)
    turno = _turno(session, ids, datetime(2028, 1, 5, 9, 0, tzinfo=TZ_CONSULTORIO))
    servicio.cambiar_estado(turno.id, "cancelado")
    session.commit()

    resultado = servicio.listar(desde=LUNES, hasta=DOMINGO)

    assert turno.id in _ids(resultado)
    assert next(t for t in resultado if t.id == turno.id).estado == "cancelado"


def test_rango_combinado_con_profesional_y_sillon(session: Session) -> None:
    ids = _seed_ids(session)
    servicio = TurnoService(session)
    del_prof_a = _turno(
        session,
        ids,
        datetime(2028, 1, 6, 9, 0, tzinfo=TZ_CONSULTORIO),
        sillon="sillon_a",
        profesional="prof_a",
    )
    del_prof_b = _turno(
        session,
        ids,
        datetime(2028, 1, 6, 10, 0, tzinfo=TZ_CONSULTORIO),
        sillon="sillon_a",
        profesional="prof_b",
    )

    solo_prof_a = servicio.listar(desde=LUNES, hasta=DOMINGO, profesional_id=ids["prof_a"].id)
    prof_b_en_sillon_b = servicio.listar(
        desde=LUNES,
        hasta=DOMINGO,
        profesional_id=ids["prof_b"].id,
        sillon_id=ids["sillon_b"].id,
    )

    assert _ids(solo_prof_a) == {del_prof_a.id}
    assert _ids(prof_b_en_sillon_b) == set()
    assert del_prof_b.id not in _ids(solo_prof_a)


def test_rango_ordena_por_inicio_sillon_e_id(session: Session) -> None:
    ids = _seed_ids(session)
    servicio = TurnoService(session)
    diez = datetime(2028, 1, 7, 10, 0, tzinfo=TZ_CONSULTORIO)

    # Mismo `inicio` en dos sillones distintos: el desempate es `sillon_id`.
    primero = _turno(session, ids, diez, sillon="sillon_a", profesional="prof_a")
    segundo = _turno(session, ids, diez, sillon="sillon_b", profesional="prof_b")
    # Un turno anterior: el orden primario es `inicio`.
    previo = _turno(
        session,
        ids,
        diez - timedelta(hours=1),
        sillon="sillon_b",
        profesional="prof_b",
    )

    primera_lectura = servicio.listar(desde=LUNES, hasta=DOMINGO)
    segunda_lectura = servicio.listar(desde=LUNES, hasta=DOMINGO)

    clave = [(t.inicio, t.sillon_id, t.id) for t in primera_lectura]
    assert clave == sorted(clave)
    assert [t.id for t in primera_lectura] == [t.id for t in segunda_lectura]

    mismo_inicio = [t for t in primera_lectura if t.inicio == diez]
    parejas = [(t.sillon_id, t.id) for t in mismo_inicio]
    assert _ids(mismo_inicio) == {primero.id, segundo.id}
    assert parejas == sorted(parejas), "a igual `inicio` debe desempatar `sillon_id`"
    assert primera_lectura[0].id == previo.id, "el orden primario es `inicio`"


# --- 3.3 TRIANGULATE -------------------------------------------------------


def test_rango_de_un_solo_dia_devuelve_solo_ese_dia(session: Session) -> None:
    ids = _seed_ids(session)
    servicio = TurnoService(session)
    sabado = _turno(session, ids, datetime(2028, 1, 8, 9, 0, tzinfo=TZ_CONSULTORIO))
    domingo = _turno(
        session,
        ids,
        datetime(2028, 1, 9, 9, 0, tzinfo=TZ_CONSULTORIO),
        sillon="sillon_b",
        profesional="prof_b",
    )

    resultado = servicio.listar(desde=date(2028, 1, 8), hasta=date(2028, 1, 8))

    assert _ids(resultado) == {sabado.id}
    assert domingo.id not in _ids(resultado)


def test_rango_de_31_dias_incluye_el_ultimo_dia_y_excluye_el_siguiente(
    session: Session,
) -> None:
    ids = _seed_ids(session)
    servicio = TurnoService(session)
    ultimo_dia = date(2028, 2, 2)
    dentro = _turno(
        session, ids, datetime(2028, 2, 2, 10, 0, tzinfo=TZ_CONSULTORIO)
    )
    fuera = _turno(
        session,
        ids,
        datetime(2028, 2, 3, 0, 0, tzinfo=TZ_CONSULTORIO),
        sillon="sillon_b",
        profesional="prof_b",
    )

    resultado = servicio.listar(desde=LUNES, hasta=ultimo_dia)

    assert (ultimo_dia - LUNES).days == 30, "31 días de calendario inclusivos"
    assert dentro.id in _ids(resultado)
    assert fuera.id not in _ids(resultado)


def test_semana_sin_turnos_devuelve_lista_vacia(session: Session) -> None:
    resultado = TurnoService(session).listar(
        desde=date(2028, 5, 1), hasta=date(2028, 5, 7)
    )

    assert resultado == []


def test_filtro_solo_por_profesional_sin_rango(session: Session) -> None:
    ids = _seed_ids(session)
    servicio = TurnoService(session)
    turno = _turno(session, ids, datetime(2028, 1, 8, 11, 0, tzinfo=TZ_CONSULTORIO))

    resultado = servicio.listar(profesional_id=ids["prof_a"].id)

    assert turno.id in _ids(resultado)
    assert all(t.profesional_id == ids["prof_a"].id for t in resultado)


def test_filtro_solo_por_sillon_sin_rango(session: Session) -> None:
    ids = _seed_ids(session)
    servicio = TurnoService(session)
    turno = _turno(session, ids, datetime(2028, 1, 8, 12, 0, tzinfo=TZ_CONSULTORIO))

    resultado = servicio.listar(sillon_id=ids["sillon_a"].id)

    assert turno.id in _ids(resultado)
    assert all(t.sillon_id == ids["sillon_a"].id for t in resultado)


def test_rango_incluye_sobreturno(session: Session) -> None:
    ids = _seed_ids(session)
    servicio = TurnoService(session)
    usuario = session.scalar(select(Usuario).where(Usuario.rol == "admin"))
    assert usuario is not None
    inicio = datetime(2028, 1, 8, 13, 0, tzinfo=TZ_CONSULTORIO)
    normal = _turno(session, ids, inicio)
    sobreturno = servicio.crear_sobreturno(
        SobreturnoCreate(
            paciente_id=ids["paciente"].id,
            profesional_id=ids["prof_a"].id,
            sillon_id=ids["sillon_a"].id,
            prestacion="Urgencia",
            inicio=inicio,
            duracion_min=30,
            motivo_sobreturno="Dolor agudo",
        ),
        usuario.id,
    )
    session.commit()

    resultado = servicio.listar(desde=LUNES, hasta=DOMINGO)

    assert _ids(resultado) >= {normal.id, sobreturno.id}
    assert next(t for t in resultado if t.id == sobreturno.id).es_sobreturno is True
