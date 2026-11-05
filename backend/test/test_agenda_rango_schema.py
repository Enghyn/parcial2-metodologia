"""TDD C-09b grupo 2 — `FiltroTurnos`: rango de días ART y `extra="forbid"` (R1).

Casos de 2.1 (rojo): semana válida, un solo extremo, rango invertido, rango
excesivo, `fecha` + rango y campo desconocido.
"""
from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.agenda.schemas import FiltroTurnos


def test_semana_valida_acepta_desde_y_hasta() -> None:
    filtro = FiltroTurnos(desde=date(2027, 1, 4), hasta=date(2027, 1, 10))

    assert filtro.desde == date(2027, 1, 4)
    assert filtro.hasta == date(2027, 1, 10)
    assert filtro.fecha is None
    assert filtro.profesional_id is None
    assert filtro.sillon_id is None


def test_solo_desde_es_invalido() -> None:
    with pytest.raises(ValidationError) as exc:
        FiltroTurnos(desde=date(2027, 1, 4))

    assert "juntos" in str(exc.value)


def test_solo_hasta_es_invalido() -> None:
    with pytest.raises(ValidationError) as exc:
        FiltroTurnos(hasta=date(2027, 1, 10))

    assert "juntos" in str(exc.value)


def test_desde_posterior_a_hasta_es_invalido() -> None:
    with pytest.raises(ValidationError) as exc:
        FiltroTurnos(desde=date(2027, 1, 10), hasta=date(2027, 1, 4))

    assert "posterior" in str(exc.value)


def test_rango_de_32_dias_es_invalido() -> None:
    # 2027-01-04 + 31 días = 2027-02-04 → 32 días de calendario.
    with pytest.raises(ValidationError) as exc:
        FiltroTurnos(desde=date(2027, 1, 4), hasta=date(2027, 2, 4))

    assert "31" in str(exc.value)


def test_fecha_junto_al_rango_es_invalido() -> None:
    with pytest.raises(ValidationError) as exc:
        FiltroTurnos(
            fecha=date(2027, 1, 6),
            desde=date(2027, 1, 4),
            hasta=date(2027, 1, 10),
        )

    assert "excluyentes" in str(exc.value)


def test_fecha_junto_a_un_solo_extremo_es_invalido() -> None:
    with pytest.raises(ValidationError) as exc:
        FiltroTurnos(fecha=date(2027, 1, 6), desde=date(2027, 1, 4))

    assert "excluyentes" in str(exc.value)


def test_campo_extra_rechazado_por_extra_forbid() -> None:
    assert FiltroTurnos.model_config.get("extra") == "forbid"

    with pytest.raises(ValidationError) as exc:
        FiltroTurnos(desde=date(2027, 1, 4), hasta=date(2027, 1, 10), foo="bar")

    assert "extra_forbidden" in str(exc.value)


def test_rango_de_31_dias_es_valido() -> None:
    filtro = FiltroTurnos(desde=date(2027, 1, 4), hasta=date(2027, 2, 3))

    assert (filtro.hasta - filtro.desde).days == 30


# --- 2.3 TRIANGULATE -------------------------------------------------------


def test_rango_de_un_solo_dia_es_valido() -> None:
    filtro = FiltroTurnos(desde=date(2027, 1, 4), hasta=date(2027, 1, 4))

    assert filtro.desde == filtro.hasta == date(2027, 1, 4)


def test_rango_que_cruza_el_29_de_febrero_es_valido() -> None:
    filtro = FiltroTurnos(desde=date(2028, 2, 28), hasta=date(2028, 3, 1))

    assert (filtro.hasta - filtro.desde).days == 2
    assert filtro.hasta == date(2028, 3, 1)


def test_fecha_sola_es_valida() -> None:
    filtro = FiltroTurnos(fecha=date(2027, 1, 6))

    assert filtro.fecha == date(2027, 1, 6)
    assert filtro.desde is None
    assert filtro.hasta is None


def test_sin_filtros_es_valido() -> None:
    filtro = FiltroTurnos()

    assert filtro.fecha is None
    assert filtro.desde is None
    assert filtro.hasta is None
    assert filtro.profesional_id is None
    assert filtro.sillon_id is None


def test_filtros_de_recurso_acompanan_al_rango() -> None:
    profesional_id = uuid4()
    sillon_id = uuid4()

    filtro = FiltroTurnos(
        desde=date(2027, 1, 4),
        hasta=date(2027, 1, 10),
        profesional_id=profesional_id,
        sillon_id=sillon_id,
    )

    assert filtro.profesional_id == profesional_id
    assert filtro.sillon_id == sillon_id
