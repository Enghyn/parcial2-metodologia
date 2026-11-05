"""TDD C-06 grupo 2 — helpers puros de slots (sin DB)."""
from datetime import UTC, datetime, time
from types import SimpleNamespace
from uuid import uuid4

from app.modules.public.service import generar_inicios, slot_libre


def _turno(sillon_id, profesional_id, inicio, fin, estado="reservado", deleted_at=None):
    return SimpleNamespace(
        sillon_id=sillon_id,
        profesional_id=profesional_id,
        inicio=inicio,
        fin=fin,
        estado=estado,
        deleted_at=deleted_at,
    )


def _bloqueo(sillon_id, profesional_id, desde, hasta):
    return SimpleNamespace(sillon_id=sillon_id, profesional_id=profesional_id, desde=desde, hasta=hasta)


def _retencion(sillon_id, profesional_id, inicio, fin, estado="vigente", expira_en=None):
    from datetime import timedelta

    from app.core.timezone import ahora

    if expira_en is None:
        expira_en = ahora() + timedelta(minutes=10)
    return SimpleNamespace(
        sillon_id=sillon_id,
        profesional_id=profesional_id,
        inicio=inicio,
        fin=fin,
        estado=estado,
        expira_en=expira_en,
    )


def test_generar_inicios_grilla_completa() -> None:
    assert generar_inicios(time(8, 0), time(10, 0), 30, 30) == [
        time(8, 0),
        time(8, 30),
        time(9, 0),
        time(9, 30),
    ]


def test_generar_inicios_duracion_mayor_que_grilla() -> None:
    assert generar_inicios(time(8, 0), time(10, 0), 30, 45) == [
        time(8, 0),
        time(8, 30),
        time(9, 0),
    ]


def test_generar_inicios_slot_no_cabe() -> None:
    assert generar_inicios(time(8, 0), time(8, 30), 30, 60) == []


def test_generar_inicios_grid_invalido() -> None:
    assert generar_inicios(time(8, 0), time(10, 0), 0, 30) == []
    assert generar_inicios(time(8, 0), time(10, 0), 30, 0) == []


def test_generar_inicios_jornada_vacia() -> None:
    assert generar_inicios(time(8, 0), time(8, 0), 30, 30) == []


def test_slot_libre_sin_ocupacion() -> None:
    assert slot_libre([], [], uuid4(), uuid4(), datetime(2027, 6, 1, 9, tzinfo=UTC), datetime(2027, 6, 1, 9, 30, tzinfo=UTC))


def test_slot_libre_turno_ocupa_sillon() -> None:
    sillon = uuid4()
    inicio = datetime(2027, 6, 1, 9, tzinfo=UTC)
    fin = datetime(2027, 6, 1, 9, 30, tzinfo=UTC)
    turnos = [_turno(sillon, uuid4(), inicio, fin)]
    assert not slot_libre(turnos, [], sillon, uuid4(), inicio, fin)


def test_slot_libre_mismo_profesional_otro_sillon() -> None:
    prof = uuid4()
    inicio = datetime(2027, 6, 1, 9, tzinfo=UTC)
    fin = datetime(2027, 6, 1, 9, 30, tzinfo=UTC)
    turnos = [_turno(uuid4(), prof, inicio, fin)]
    assert not slot_libre(turnos, [], uuid4(), prof, inicio, fin)


def test_slot_libre_otro_sillon_y_profesional() -> None:
    inicio = datetime(2027, 6, 1, 9, tzinfo=UTC)
    fin = datetime(2027, 6, 1, 9, 30, tzinfo=UTC)
    turnos = [_turno(uuid4(), uuid4(), inicio, fin)]
    assert slot_libre(turnos, [], uuid4(), uuid4(), inicio, fin)


def test_slot_libre_turno_cancelado_libera() -> None:
    sillon = uuid4()
    prof = uuid4()
    inicio = datetime(2027, 6, 1, 9, tzinfo=UTC)
    fin = datetime(2027, 6, 1, 9, 30, tzinfo=UTC)
    turnos = [_turno(sillon, prof, inicio, fin, estado="cancelado")]
    assert slot_libre(turnos, [], sillon, prof, inicio, fin)


def test_slot_libre_turno_softdeleted_libera() -> None:
    sillon = uuid4()
    prof = uuid4()
    inicio = datetime(2027, 6, 1, 9, tzinfo=UTC)
    fin = datetime(2027, 6, 1, 9, 30, tzinfo=UTC)
    turnos = [_turno(sillon, prof, inicio, fin, deleted_at=datetime(2027, 1, 1, tzinfo=UTC))]
    assert slot_libre(turnos, [], sillon, prof, inicio, fin)


def test_slot_libre_bloqueo_excluye_sillon() -> None:
    sillon = uuid4()
    inicio = datetime(2027, 6, 1, 9, tzinfo=UTC)
    fin = datetime(2027, 6, 1, 9, 30, tzinfo=UTC)
    bloqueos = [_bloqueo(sillon, None, inicio, fin)]
    assert not slot_libre([], bloqueos, sillon, uuid4(), inicio, fin)


def test_slot_libre_bloqueo_profesional_excluye() -> None:
    prof = uuid4()
    inicio = datetime(2027, 6, 1, 9, tzinfo=UTC)
    fin = datetime(2027, 6, 1, 9, 30, tzinfo=UTC)
    bloqueos = [_bloqueo(None, prof, inicio, fin)]
    assert not slot_libre([], bloqueos, uuid4(), prof, inicio, fin)


def test_slot_libre_retencion_vigente_mismo_sillon_false() -> None:
    sillon = uuid4()
    prof_ret = uuid4()
    prof = uuid4()
    inicio = datetime(2027, 6, 2, 9, tzinfo=UTC)
    fin = datetime(2027, 6, 2, 9, 30, tzinfo=UTC)
    retenciones = [_retencion(sillon, prof_ret, inicio, fin)]
    assert not slot_libre([], [], sillon, uuid4(), inicio, fin, retenciones=retenciones)


def test_slot_libre_retencion_vigente_mismo_profesional_false() -> None:
    sillon_ret = uuid4()
    prof = uuid4()
    inicio = datetime(2027, 6, 2, 10, tzinfo=UTC)
    fin = datetime(2027, 6, 2, 10, 30, tzinfo=UTC)
    retenciones = [_retencion(sillon_ret, prof, inicio, fin)]
    assert not slot_libre([], [], uuid4(), prof, inicio, fin, retenciones=retenciones)


def test_slot_libre_retencion_vencida_true() -> None:
    from datetime import timedelta

    from app.core.timezone import ahora

    sillon = uuid4()
    prof = uuid4()
    inicio = datetime(2027, 6, 2, 11, tzinfo=UTC)
    fin = datetime(2027, 6, 2, 11, 30, tzinfo=UTC)
    retenciones = [
        _retencion(sillon, prof, inicio, fin, expira_en=ahora() - timedelta(minutes=1))
    ]
    assert slot_libre([], [], sillon, prof, inicio, fin, retenciones=retenciones)


def test_slot_libre_retencion_otro_recurso_true() -> None:
    sillon = uuid4()
    prof = uuid4()
    inicio = datetime(2027, 6, 2, 12, tzinfo=UTC)
    fin = datetime(2027, 6, 2, 12, 30, tzinfo=UTC)
    retenciones = [_retencion(uuid4(), uuid4(), inicio, fin)]
    assert slot_libre([], [], sillon, prof, inicio, fin, retenciones=retenciones)
