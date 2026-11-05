"""Tests puros del generador de QR (C-10, D7)."""
from __future__ import annotations

from uuid import UUID

import pytest

from app.modules.public.qr import svg_qr, url_reserva, url_turno


def test_url_reserva_construye_la_url_esperada():
    assert url_reserva("https://example.com") == "https://example.com/reservar"
    assert url_reserva("https://example.com/") == "https://example.com/reservar"
    assert url_reserva("https://example.com/portal") == "https://example.com/portal/reservar"


def test_url_turno_construye_la_url_con_token_en_path():
    tok = UUID("12345678-1234-5678-1234-567812345678")
    assert url_turno("https://example.com", tok) == "https://example.com/p/turno/12345678-1234-5678-1234-567812345678"
    assert url_turno("https://example.com/", "abc") == "https://example.com/p/turno/abc"


def test_svg_qr_devuelve_svg_valido():
    svg = svg_qr("https://example.com/reservar")
    assert "<svg" in svg
    assert "viewBox" in svg or "viewbox" in svg.lower()


def test_svg_qr_es_determinista():
    a = svg_qr("https://example.com/reservar")
    b = svg_qr("https://example.com/reservar")
    assert a == b


def test_svg_qr_no_contiene_datos_sensibles():
    svg = svg_qr("https://example.com/reservar")
    # el QR es una representación gráfica: no lleva DNI ni nombre como texto
    assert "dni" not in svg.lower()


def test_base_con_path_se_conserva():
    url = url_reserva("https://dominio/portal")
    assert url == "https://dominio/portal/reservar"
    svg = svg_qr(url)
    assert "<svg" in svg
