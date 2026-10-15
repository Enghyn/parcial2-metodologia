"""Agregador de routers /api/v1 (vacío hasta C-05+).

Los routers viven en `app.modules.<dominio>.router` y se montan acá con
`include_router` en su change dueño.

TODO(C-05): primer `include_router` (agenda). Nace vacío a propósito.
"""

from fastapi import APIRouter

router = APIRouter()

__all__ = ["router"]
