"""Generación local de QR en SVG (C-10, D7)."""
from __future__ import annotations

import io
from uuid import UUID

import segno


def _base(base: str) -> str:
    return base.rstrip("/")


def url_reserva(base: str) -> str:
    return f"{_base(base)}/reservar"


def url_turno(base: str, token: UUID | str) -> str:
    return f"{_base(base)}/p/turno/{token}"


def svg_qr(url: str) -> str:
    qr = segno.make(url)
    buffer = io.BytesIO()
    qr.save(buffer, kind="svg", omitsize=True)
    return buffer.getvalue().decode("utf-8")


__all__ = ["svg_qr", "url_reserva", "url_turno"]