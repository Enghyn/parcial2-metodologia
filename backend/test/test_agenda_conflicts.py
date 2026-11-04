"""TDD C-04 grupo 2 — helpers puros de solapamiento (sin DB).

`solapamiento` y `detectar_conflicto` viven en `app.modules.agenda.service` y
no importan FastAPI ni SQLAlchemy session: se testean con entidades en memoria.
"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.modules.agenda.models import Bloqueo, Turno
from app.modules.agenda.service import detectar_conflicto, solapamiento


def _dt(hora: int, minuto: int = 0) -> datetime:
    return datetime(2026, 11, 3, hora, minuto, tzinfo=timezone.utc)


def test_solapamiento_true() -> None:
    # 10:00-10:30 vs 10:15-10:45 → solape
    assert solapamiento(_dt(10, 0), _dt(10, 30), _dt(10, 15), _dt(10, 45)) is True


def test_solapamiento_false_sin_solape() -> None:
    # 10:00-10:30 vs 11:00-11:30 → sin solape
    assert solapamiento(_dt(10, 0), _dt(10, 30), _dt(11, 0), _dt(11, 30)) is False


def test_solapamiento_tangencia_false() -> None:
    # fin_a == inicio_b → tangencia, no cuenta como solape
    assert solapamiento(_dt(10, 0), _dt(10, 30), _dt(10, 30), _dt(11, 0)) is False


def test_solapamiento_contencion_true() -> None:
    # un rango contenido en el otro
    assert solapamiento(_dt(10, 0), _dt(11, 0), _dt(10, 15), _dt(10, 30)) is True


def _turno(
    *,
    sillon_id,
    profesional_id,
    inicio: datetime,
    fin: datetime,
    estado: str = "reservado",
    deleted: bool = False,
) -> Turno:
    t = Turno(
        id=uuid4(),
        paciente_id=uuid4(),
        profesional_id=profesional_id,
        sillon_id=sillon_id,
        prestacion="Consulta",
        inicio=inicio,
        fin=fin,
        duracion_min=int((fin - inicio).total_seconds() // 60),
        estado=estado,
        token_publico=uuid4(),
        sena_monto=0,
    )
    if deleted:
        from datetime import datetime as _dt2, timezone as _tz

        t.deleted_at = _dt2.now(_tz.utc)
    return t


def test_detectar_conflicto_hueco_libre_none() -> None:
    sillon = uuid4()
    prof = uuid4()
    inicio = _dt(10, 0)
    fin = _dt(10, 30)
    assert detectar_conflicto([], [], sillon, prof, inicio, fin) is None


def test_detectar_conflicto_mismo_sillon() -> None:
    sillon = uuid4()
    prof_a = uuid4()
    prof_b = uuid4()
    inicio = _dt(10, 0)
    fin = _dt(10, 30)
    t = _turno(
        sillon_id=sillon,
        profesional_id=prof_a,
        inicio=_dt(10, 15),
        fin=_dt(10, 45),
    )
    res = detectar_conflicto([t], [], sillon, prof_b, inicio, fin)
    assert res == "sillon"


def test_detectar_conflicto_mismo_profesional_distinto_sillon() -> None:
    sillon_a = uuid4()
    sillon_b = uuid4()
    prof = uuid4()
    inicio = _dt(10, 0)
    fin = _dt(10, 30)
    t = _turno(
        sillon_id=sillon_a,
        profesional_id=prof,
        inicio=_dt(10, 15),
        fin=_dt(10, 45),
    )
    res = detectar_conflicto([t], [], sillon_b, prof, inicio, fin)
    assert res == "profesional"


def test_detectar_conflicto_bloqueo() -> None:
    sillon = uuid4()
    prof = uuid4()
    inicio = _dt(10, 0)
    fin = _dt(10, 30)
    b = Bloqueo(
        id=uuid4(),
        sillon_id=sillon,
        profesional_id=None,
        desde=_dt(10, 15),
        hasta=_dt(10, 45),
        motivo="Limpieza",
    )
    res = detectar_conflicto([], [b], sillon, prof, inicio, fin)
    assert res == "bloqueo"


def test_detectar_conflicto_cancelado_no_cuenta() -> None:
    sillon = uuid4()
    prof_a = uuid4()
    prof_b = uuid4()
    inicio = _dt(10, 0)
    fin = _dt(10, 30)
    t = _turno(
        sillon_id=sillon,
        profesional_id=prof_a,
        inicio=_dt(10, 15),
        fin=_dt(10, 45),
        estado="cancelado",
    )
    assert detectar_conflicto([t], [], sillon, prof_b, inicio, fin) is None


def test_detectar_conflicto_borrado_no_cuenta() -> None:
    sillon = uuid4()
    prof_a = uuid4()
    prof_b = uuid4()
    inicio = _dt(10, 0)
    fin = _dt(10, 30)
    t = _turno(
        sillon_id=sillon,
        profesional_id=prof_a,
        inicio=_dt(10, 15),
        fin=_dt(10, 45),
        deleted=True,
    )
    assert detectar_conflicto([t], [], sillon, prof_b, inicio, fin) is None


def test_detectar_conflicto_prioriza_sillon_sobre_profesional() -> None:
    # mismo turno comparte ambos recursos → reporta sillón
    sillon = uuid4()
    prof = uuid4()
    inicio = _dt(10, 0)
    fin = _dt(10, 30)
    t = _turno(
        sillon_id=sillon,
        profesional_id=prof,
        inicio=_dt(10, 15),
        fin=_dt(10, 45),
    )
    res = detectar_conflicto([t], [], sillon, prof, inicio, fin)
    assert res == "sillon"