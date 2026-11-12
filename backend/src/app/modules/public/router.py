"""Router público (C-06/C-10): endpoints sin autenticación y validación estricta."""
from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.rate_limit import limitar_publico
from app.db.session import get_db
from app.modules.public.portal_service import PortalPublicoService
from app.modules.public.qr import svg_qr, url_reserva, url_turno
from app.modules.public.schemas import (
    AprobacionPublicaIn,
    ConfirmarPublicoIn,
    PagoPublicoOut,
    PreReservaCreate,
    PreReservaOut,
    PresupuestoPublicoOut,
    ProfesionalPublicoOut,
    PublicTurnoOut,
    RechazoPublicoIn,
    ReprogramarPublico,
    ReservaCreate,
    SlotOut,
)
from app.modules.public.service import PublicReservaService

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/profesionales", response_model=list[ProfesionalPublicoOut])
def listar_profesionales(db: Annotated[Session, Depends(get_db)]) -> list[ProfesionalPublicoOut]:
    return PublicReservaService(db).listar_profesionales()


@router.get("/disponibilidad", response_model=list[SlotOut], dependencies=[Depends(limitar_publico("lectura"))])
def consultar_disponibilidad(
    db: Annotated[Session, Depends(get_db)],
    fecha: Annotated[date, Query()],
    duracion_min: Annotated[int, Query(gt=0)] = 30,
    profesional_id: Annotated[UUID | None, Query()] = None,
) -> list[SlotOut]:
    return PublicReservaService(db).disponibilidad(
        fecha=fecha, duracion_min=duracion_min, profesional_id=profesional_id
    )


@router.post("/pre-reservas", response_model=PreReservaOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(limitar_publico("escritura"))])
def crear_pre_reserva(
    datos: PreReservaCreate,
    db: Annotated[Session, Depends(get_db)],
) -> PreReservaOut:
    servicio = PublicReservaService(db)
    pr = servicio.crear_pre_reserva(datos)
    return PreReservaOut(
        pre_reserva_token=pr.token,
        inicio=pr.inicio,
        fin=pr.fin,
        duracion_min=pr.duracion_min,
        expira_en=pr.expira_en,
    )


@router.post("/reservar", response_model=PublicTurnoOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(limitar_publico("escritura"))])
def reservar(
    datos: ReservaCreate,
    db: Annotated[Session, Depends(get_db)],
) -> PublicTurnoOut:
    servicio = PublicReservaService(db)
    turno = servicio.reservar(datos)
    return servicio.to_public(turno)


@router.get("/turnos/{token}", response_model=PublicTurnoOut)
def obtener_turno(
    token: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> PublicTurnoOut:
    servicio = PublicReservaService(db)
    return servicio.to_public(servicio.obtener_por_token(token))


@router.post("/turnos/{token}/cancelar", response_model=PublicTurnoOut, dependencies=[Depends(limitar_publico("escritura"))])
def cancelar_turno(
    token: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> PublicTurnoOut:
    servicio = PublicReservaService(db)
    return servicio.to_public(servicio.cancelar_por_token(token))


@router.post("/turnos/{token}/reprogramar", response_model=PublicTurnoOut, dependencies=[Depends(limitar_publico("escritura"))])
def reprogramar_turno(
    token: UUID,
    datos: ReprogramarPublico,
    db: Annotated[Session, Depends(get_db)],
) -> PublicTurnoOut:
    servicio = PublicReservaService(db)
    turno = servicio.reprogramar_por_token(token, datos)
    return servicio.to_public(turno)


# --- Portal público de presupuestos y pagos (C-18, D5/R9) ---
# Todo se identifica por `token_publico` opaco; nunca por IDs internos.


@router.get(
    "/presupuestos/{token}",
    response_model=PresupuestoPublicoOut,
    dependencies=[Depends(limitar_publico("lectura"))],
)
def obtener_presupuesto_publico(
    token: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> PresupuestoPublicoOut:
    return PortalPublicoService(db).obtener_presupuesto_publico(token)


@router.post(
    "/presupuestos/{token}/aprobar",
    response_model=PresupuestoPublicoOut,
    dependencies=[Depends(limitar_publico("escritura"))],
)
def aprobar_presupuesto_publico(
    token: UUID,
    datos: AprobacionPublicaIn,
    db: Annotated[Session, Depends(get_db)],
) -> PresupuestoPublicoOut:
    return PortalPublicoService(db).aprobar(token, datos.firma)


@router.post(
    "/presupuestos/{token}/rechazar",
    response_model=PresupuestoPublicoOut,
    dependencies=[Depends(limitar_publico("escritura"))],
)
def rechazar_presupuesto_publico(
    token: UUID,
    db: Annotated[Session, Depends(get_db)],
    datos: RechazoPublicoIn | None = None,
) -> PresupuestoPublicoOut:
    return PortalPublicoService(db).rechazar(token, datos.motivo if datos else None)


@router.get(
    "/pagos/{token}",
    response_model=PagoPublicoOut,
    dependencies=[Depends(limitar_publico("lectura"))],
)
def obtener_pago_publico(
    token: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> PagoPublicoOut:
    return PortalPublicoService(db).obtener_pago_publico(token)


@router.post(
    "/pagos/{token}/confirmar",
    response_model=PagoPublicoOut,
    dependencies=[Depends(limitar_publico("escritura"))],
)
def confirmar_pago_publico(
    token: UUID,
    db: Annotated[Session, Depends(get_db)],
    datos: ConfirmarPublicoIn | None = None,
) -> PagoPublicoOut:
    return PortalPublicoService(db).confirmar_pago_publico(token, datos)


@router.get("/qr/reserva.svg", dependencies=[Depends(limitar_publico("lectura"))])
def qr_reserva() -> Response:
    settings = get_settings()
    url = url_reserva(settings.public_base_url)
    return Response(content=svg_qr(url), media_type="image/svg+xml")


@router.get("/turnos/{token}/qr.svg", dependencies=[Depends(limitar_publico("lectura"))])
def qr_turno(
    token: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    servicio = PublicReservaService(db)
    turno = servicio.obtener_por_token(token)  # 404 if not exists
    settings = get_settings()
    url = url_turno(settings.public_base_url, turno.token_publico)
    resp = Response(content=svg_qr(url), media_type="image/svg+xml")
    resp.headers["Cache-Control"] = "no-store"
    return resp


__all__ = ["router"]