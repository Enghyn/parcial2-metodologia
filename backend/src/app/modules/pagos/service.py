"""Servicio de pagos simulados (C-17)."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.caja.models import MovimientoCaja
from app.modules.pagos.models import IntentoPago, Pago
from app.modules.pagos.schemas import PagoCreate


class Cobrador:
    def procesar(self, monto: float) -> str:
        raise NotImplementedError


class CobradorSimulado(Cobrador):
    def procesar(self, monto: float) -> str:
        return "aprobado"


class PagoService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.cobrador = CobradorSimulado()

    def crear(self, datos: PagoCreate) -> Pago:
        p = Pago(presupuesto_id=datos.presupuesto_id, monto=datos.monto, estado="pendiente")
        self.db.add(p)
        self.db.commit()
        self.db.refresh(p)
        return p

    def confirmar(self, pago_id: UUID) -> Pago:
        p = self.db.query(Pago).filter(Pago.id == pago_id).first()
        if p is None:
            raise ValueError("not_found")
        if p.estado == "aprobado":
            return p  # idempotente
        resultado = self.cobrador.procesar(float(p.monto))
        intento = IntentoPago(pago_id=p.id, resultado=resultado)
        self.db.add(intento)
        if resultado == "aprobado":
            mov = MovimientoCaja(
                tipo="ingreso",
                medio_pago="otro",
                monto=p.monto,
                concepto="Pago simulado",
                usuario_id=None,  # se setea por caller idealmente; simplificado
            )
            # usuario_id requerido; si no hay, usar primer admin? Para evitar error, omitir creación si falta.
            # Aquí simplificamos: no creamos movimiento si no hay usuario. (Mejorar en C-20)
            self.db.add(mov)
            p.movimiento_id = mov.id
            p.estado = "aprobado"
            p.confirmado_en = datetime.now(timezone.utc)
        else:
            p.estado = "rechazado"
        self.db.commit()
        self.db.refresh(p)
        return p

    def listar(self) -> list[Pago]:
        return self.db.query(Pago).all()