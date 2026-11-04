"""Zona canónica del consultorio: America/Argentina/Buenos_Aires (UTC-3)."""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

TZ_CONSULTORIO = ZoneInfo("America/Argentina/Buenos_Aires")


def ahora() -> datetime:
    """Instante actual en la zona del consultorio."""
    return datetime.now(TZ_CONSULTORIO)


def inicio_dia(fecha: date) -> datetime:
    """00:00 ART de la fecha indicada."""
    return datetime.combine(fecha, time.min, tzinfo=TZ_CONSULTORIO)


def fin_dia(fecha: date) -> datetime:
    """00:00 ART del día siguiente (fin exclusivo)."""
    return inicio_dia(fecha) + timedelta(days=1)


def combinar(fecha: date, hora: time) -> datetime:
    """Fecha + hora de pared interpretadas en ART."""
    return datetime.combine(fecha, hora, tzinfo=TZ_CONSULTORIO)


def normalizar_entrada(valor: datetime) -> datetime:
    """Un datetime naive se interpreta como ART; uno aware se respeta."""
    if valor.tzinfo is None:
        return valor.replace(tzinfo=TZ_CONSULTORIO)
    return valor


__all__ = [
    "TZ_CONSULTORIO",
    "ahora",
    "combinar",
    "fin_dia",
    "inicio_dia",
    "normalizar_entrada",
]
