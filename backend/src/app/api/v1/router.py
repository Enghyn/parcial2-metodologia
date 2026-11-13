"""Agregador de routers /api/v1.

Los routers viven en `app.modules.<dominio>.router` y se montan acá con
`include_router` en su change dueña.

C-03: monta `auth` (login + me).

TODO(C-04): montar agenda (y en C-07 clinica, C-08 caja). El agregador sigue
siendo el punto único de montaje hasta cerrar todos los módulos.
"""

from fastapi import APIRouter

from app.modules.admin.router import router as admin_router
from app.modules.agenda.router import router as agenda_router
from app.modules.audit.router import router as audit_router
from app.modules.auth.router import router as auth_router
from app.modules.caja.router import router as caja_router
from app.modules.clinica.router import router as clinica_router
from app.modules.comprobante.router import router as comprobante_router
from app.modules.lista_espera.router import router as lista_espera_router
from app.modules.nomenclador.router import router as nomenclador_router
from app.modules.notificaciones.router import router as notificaciones_router
from app.modules.os.router import router as os_router
from app.modules.pagos.router import router as pagos_router
from app.modules.presupuestos.router import router as presupuestos_router
from app.modules.public.router import router as public_router

router = APIRouter()
router.include_router(admin_router)
router.include_router(auth_router)
router.include_router(audit_router)
router.include_router(agenda_router)
router.include_router(caja_router)
router.include_router(clinica_router)
router.include_router(comprobante_router)
router.include_router(lista_espera_router)
router.include_router(nomenclador_router)
router.include_router(notificaciones_router)
router.include_router(os_router)
router.include_router(pagos_router)
router.include_router(presupuestos_router)
router.include_router(public_router)

__all__ = ["router"]
