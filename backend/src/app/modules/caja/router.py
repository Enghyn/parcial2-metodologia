"""Router de caja (C-08 + C-12): movimientos, cierres, cuenta corriente, ajustes, export."""
from __future__ import annotations

import csv
import io
from datetime import date
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.core.timezone import ahora
from app.db.session import get_db
from app.modules.admin.models import Usuario
from app.modules.caja.models import (
    CuentaCorrientePaciente,
)
from app.modules.caja.schemas import (
    AjusteCreate,
    AjusteOut,
    CierreCreate,
    CierreOut,
    CuentaCorrienteOut,
    CuentaCorrienteResumen,
    MovimientoCreate,
    MovimientoCuentaCorriente,
    MovimientoOut,
    ResumenDiarioOut,
)
from app.modules.caja.service import (
    AjusteService,
    CajaService,
    CierreService,
    CuentaCorrienteService,
)

router = APIRouter(prefix="/caja", tags=["caja"])

_ROLES_CAJA = ("admin", "recepcion")
_ROLES_ADMIN = ("admin",)


@router.post(
    "/movimientos",
    response_model=MovimientoOut,
    status_code=status.HTTP_201_CREATED,
)
def crear_movimiento(
    datos: MovimientoCreate,
    db: Annotated[Session, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(require_role(*_ROLES_CAJA))],
) -> MovimientoOut:
    """Registra un movimiento. Rechaza 409 si el día está cerrado (bloqueo de período)."""
    movimiento = CajaService(db).registrar(datos, usuario.id)
    return MovimientoOut.model_validate(movimiento)


@router.get(
    "/movimientos",
    response_model=list[MovimientoOut],
    dependencies=[Depends(require_role(*_ROLES_CAJA))],
)
def listar_movimientos(
    db: Annotated[Session, Depends(get_db)],
    fecha: Annotated[date | None, Query()] = None,
) -> list[MovimientoOut]:
    return [MovimientoOut.model_validate(m) for m in CajaService(db).listar(fecha)]


@router.get(
    "/resumen-diario",
    response_model=ResumenDiarioOut,
    dependencies=[Depends(require_role(*_ROLES_CAJA))],
)
def resumen_diario(
    db: Annotated[Session, Depends(get_db)],
    fecha: Annotated[date | None, Query()] = None,
) -> ResumenDiarioOut:
    return CajaService(db).resumen(fecha)


# --- C-12: Cierre diario ---


@router.post(
    "/cierres",
    response_model=CierreOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(*_ROLES_ADMIN))],
)
def cerrar_caja(
    datos: CierreCreate,
    db: Annotated[Session, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(require_role(*_ROLES_ADMIN))],
) -> CierreOut:
    """Cierra el día calendario (solo admin). 409 si el día ya está cerrado."""
    cierre = CierreService(db).cerrar(datos, usuario.id)
    return CierreOut.model_validate(cierre)


@router.get(
    "/cierres",
    response_model=list[CierreOut],
    dependencies=[Depends(require_role(*_ROLES_CAJA))],
)
def listar_cierres(
    db: Annotated[Session, Depends(get_db)],
) -> list[CierreOut]:
    return [CierreOut.model_validate(c) for c in CierreService(db).listar()]


# --- C-12: Cuenta corriente por paciente ---


@router.get(
    "/cuenta-corriente/{paciente_id}",
    response_model=CuentaCorrienteOut,
    dependencies=[Depends(require_role(*_ROLES_CAJA))],
)
def cuenta_corriente(
    paciente_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> CuentaCorrienteOut:
    """Saldo derivado y detalle de movimientos de la cuenta corriente de un paciente."""
    pid = UUID(paciente_id)
    service = CuentaCorrienteService(db)
    saldo = service.saldo(pid)
    detalle = service.detalle(pid)
    return CuentaCorrienteOut(
        paciente_id=pid,
        saldo=saldo,
        detalle=[MovimientoCuentaCorriente.model_validate(m) for m in detalle],
    )


@router.get(
    "/cuentas-corrientes",
    response_model=list[CuentaCorrienteResumen],
    dependencies=[Depends(require_role(*_ROLES_CAJA))],
)
def cuentas_corrientes(
    db: Annotated[Session, Depends(get_db)],
) -> list[CuentaCorrienteResumen]:
    """Lista pacientes con saldo distinto de cero en cuenta corriente."""
    from app.modules.clinica.models import Paciente

    stmt = (
        select(CuentaCorrientePaciente, Paciente.nombre)
        .join(Paciente, CuentaCorrientePaciente.paciente_id == Paciente.id)
        .where(CuentaCorrientePaciente.saldo != 0)
    )
    filas = list(db.execute(stmt))
    return [
        CuentaCorrienteResumen(
            paciente_id=cuenta.paciente_id,
            nombre=nombre,
            saldo=cuenta.saldo,
        )
        for cuenta, nombre in filas
    ]


# --- C-12: Ajustes auditados ---


@router.post(
    "/ajustes",
    response_model=AjusteOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(*_ROLES_ADMIN))],
)
def registrar_ajuste(
    datos: AjusteCreate,
    db: Annotated[Session, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(require_role(*_ROLES_ADMIN))],
) -> AjusteOut:
    """Registra un ajuste auditado: contra-asiento + fila en ajustes_caja (solo admin)."""
    ajuste = AjusteService(db).registrar(datos, usuario.id)
    return AjusteOut.model_validate(ajuste)


# --- C-12: Export CSV ---


@router.get(
    "/export",
    dependencies=[Depends(require_role(*_ROLES_CAJA))],
)
def export_caja_csv(
    db: Annotated[Session, Depends(get_db)],
    fecha: Annotated[date | None, Query()] = None,
) -> Response:
    """Exporta CSV del libro del día (UTF-8, ARS, sin datos clínicos)."""
    dia = fecha or ahora().date()
    movimientos = CajaService(db).listar(dia)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["fecha", "tipo", "medio_pago", "monto", "concepto", "turno_id", "usuario_id"])
    total_ingresos = Decimal(0)
    total_egresos = Decimal(0)
    for m in movimientos:
        writer.writerow(
            [
                m.fecha.isoformat(),
                m.tipo,
                m.medio_pago,
                f"{m.monto:.2f}",
                m.concepto,
                str(m.turno_id) if m.turno_id else "",
                str(m.usuario_id),
            ]
        )
        if m.tipo == "ingreso":
            total_ingresos += m.monto
        else:
            total_egresos += m.monto
    balance = total_ingresos - total_egresos
    writer.writerow([])
    writer.writerow(["TOTALES", "", "", f"{total_ingresos:.2f}", f"{total_egresos:.2f}", "", ""])
    writer.writerow(["BALANCE", "", "", f"{balance:.2f}", "", "", ""])

    content = buffer.getvalue()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="caja-{dia.isoformat()}.csv"',
        },
    )


__all__ = ["router"]