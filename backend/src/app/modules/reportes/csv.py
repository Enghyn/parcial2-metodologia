"""Formateador CSV es-AR reutilizable (C-21, reutilizado de C-12).

Formato: BOM UTF-8, separador `;`, decimales con coma, fechas `dd/mm/aaaa`,
campos escapados segun RFC 4180. Nunca incluye DNI ni datos clinicos (R9).
"""

from __future__ import annotations

import csv
import io
from datetime import date, datetime
from decimal import Decimal


def _formatear_valor(valor: object) -> str:
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, Decimal):
        return f"{valor:.2f}".replace(".", ",")
    if valor is None:
        return ""
    return str(valor)


def render_csv(columnas: list[str], filas: list[list[object]]) -> bytes:
    """Renderiza un CSV es-AR con BOM UTF-8 y separador `;`."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(columnas)
    for fila in filas:
        writer.writerow([_formatear_valor(v) for v in fila])
    content = buffer.getvalue()
    return ("\ufeff" + content).encode("utf-8")


__all__ = ["render_csv"]
