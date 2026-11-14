"""TDD C-21 — formateador CSV es-AR (unidad, sin DB)."""
from app.modules.reportes.csv import render_csv


def test_render_csv_bom_y_separador() -> None:
    import datetime

    columnas = ["fecha", "monto", "concepto"]
    filas = [[datetime.date(2026, 10, 5), "1000.00", "Consulta"]]
    contenido = render_csv(columnas, filas).decode("utf-8")
    assert contenido.startswith("\ufeff")  # BOM UTF-8
    primera = contenido.splitlines()[0]
    assert ";" in primera  # separador ;
    assert "2026-10-05" not in contenido  # fecha formateada, no iso
    assert "05/10/2026" in contenido


def test_render_csv_fecha_ddmmaaaa() -> None:
    import datetime

    columnas = ["fecha"]
    filas = [[datetime.datetime(2026, 10, 5, 9, 30)]]
    contenido = render_csv(columnas, filas).decode("utf-8")
    assert "05/10/2026" in contenido


def test_render_csv_decimal_coma() -> None:
    from decimal import Decimal

    columnas = ["monto"]
    filas = [[Decimal("1250.50")]]
    contenido = render_csv(columnas, filas).decode("utf-8")
    assert "1250,50" in contenido


def test_render_csv_escape_campos() -> None:
    columnas = ["concepto"]
    filas = [['Consulta; con "comas" y punto y coma']]
    contenido = render_csv(columnas, filas).decode("utf-8")
    linea = contenido.splitlines()[-1]
    assert '"' in linea  # campo entre comillas por contener ; y "
    assert '""' in linea  # comillas escapadas duplicadas


def test_render_csv_sin_dni_ni_clinico() -> None:
    columnas = ["turno_id", "monto"]
    filas = [[1, "500.00"]]
    contenido = render_csv(columnas, filas).decode("utf-8")
    assert "DNI" not in contenido
    assert "diagnostico" not in contenido.lower()
    assert "99999999" not in contenido


def test_render_csv_content_bytes() -> None:
    contenido = render_csv(["a"], [["x"]])
    assert isinstance(contenido, bytes)
    assert contenido.startswith(b"\xef\xbb\xbf")  # BOM bytes UTF-8
