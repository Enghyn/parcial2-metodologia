"""Agregador de routers /api/v1.

Los routers viven en `app.modules.<dominio>.router` y se montan acá con
`include_router` en su change dueña.

C-03: monta `auth` (login + me).

TODO(C-04): montar agenda (y en C-07 clinica, C-08 caja). El agregador sigue
siendo el punto único de montaje hasta cerrar todos los módulos.
"""

from fastapi import APIRouter

from app.modules.agenda.router import router as agenda_router
from app.modules.auth.router import router as auth_router
from app.modules.public.router import router as public_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(agenda_router)
router.include_router(public_router)

__all__ = ["router"]
