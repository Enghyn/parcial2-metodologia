"""Servicio de caja (C-08): libro append-only y resumen diario."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.timezone import ahora, fin_dia, inicio_dia
from app.modules.agenda.models import Turno
from app.modules.caja.models import MEDIOS_PAGO, MovimientoCaja
from app.modules.caja.schemas import MovimientoCreate, ResumenDiarioOut

_CERO = Decimal("0.00")


class CajaService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _turno_vigente(self, turno_id: UUID) -> Turno:
        turno = self.db.scalar(
            select(Turno).where(Turno.id == turno_id, Turno.deleted_at.is_(None))
        )
        if turno is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado"
            )
        return turno

    def registrar(self, datos: MovimientoCreate, usuario_id: UUID) -> MovimientoCaja:
        if datos.turno_id is not None:
            self._turno_vigente(datos.turno_id)
        movimiento = MovimientoCaja(
            tipo=datos.tipo,
            medio_pago=datos.medio_pago,
            monto=datos.monto,
            concepto=datos.concepto,
            turno_id=datos.turno_id,
            usuario_id=usuario_id,
        )
        self.db.add(movimiento)
        self.db.commit()
        self.db.refresh(movimiento)
        return movimiento

    def listar(self, fecha: date | None = None) -> list[MovimientoCaja]:
        stmt = select(MovimientoCaja)
        if fecha is not None:
            stmt = stmt.where(
                MovimientoCaja.fecha >= inicio_dia(fecha),
                MovimientoCaja.fecha < fin_dia(fecha),
            )
        return list(self.db.scalars(stmt.order_by(MovimientoCaja.fecha.desc())))

    def resumen(self, fecha: date | None = None) -> ResumenDiarioOut:
        dia = fecha or ahora().date()
        movimientos = self.listar(dia)
        total_ingresos = sum(
            (m.monto for m in movimientos if m.tipo == "ingreso"), _CERO
        )
        total_egresos = sum(
            (m.monto for m in movimientos if m.tipo == "egreso"), _CERO
        )
        por_medio = {medio: _CERO for medio in MEDIOS_PAGO}
        for movimiento in movimientos:
            if movimiento.tipo == "ingreso":
                por_medio[movimiento.medio_pago] += movimiento.monto
        return ResumenDiarioOut(
            fecha=dia,
            total_ingresos=total_ingresos,
            total_egresos=total_egresos,
            balance=total_ingresos - total_egresos,
            por_medio_pago=por_medio,
        )


__all__ = ["CajaService"]
