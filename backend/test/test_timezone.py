"""Zona canónica del consultorio: America/Argentina/Buenos_Aires."""
from datetime import UTC, date, datetime, time, timedelta

from app.core.timezone import (
    TZ_CONSULTORIO,
    ahora,
    combinar,
    fin_dia,
    inicio_dia,
    normalizar_entrada,
)


def test_09_art_es_12_utc() -> None:
    inicio = combinar(date(2027, 1, 10), time(9, 0))
    assert inicio.tzinfo == TZ_CONSULTORIO
    assert inicio.utcoffset() == timedelta(hours=-3)
    assert inicio.astimezone(UTC) == datetime(2027, 1, 10, 12, 0, tzinfo=UTC)


def test_inicio_y_fin_del_dia_art() -> None:
    inicio = inicio_dia(date(2027, 1, 10))
    fin = fin_dia(date(2027, 1, 10))
    assert inicio == datetime(2027, 1, 10, 0, 0, tzinfo=TZ_CONSULTORIO)
    assert fin - inicio == timedelta(days=1)


def test_naive_se_interpreta_como_art() -> None:
    normalizado = normalizar_entrada(datetime(2027, 1, 10, 9, 0))
    assert normalizado.tzinfo == TZ_CONSULTORIO
    assert normalizado.astimezone(UTC) == datetime(2027, 1, 10, 12, 0, tzinfo=UTC)


def test_aware_se_respeta() -> None:
    original = datetime(2027, 1, 10, 12, 0, tzinfo=UTC)
    assert normalizar_entrada(original) is original


def test_ahora_usa_la_zona_del_consultorio() -> None:
    assert ahora().tzinfo == TZ_CONSULTORIO
