"""Servicio de pagos simulados (C-17)."""
from __future__ import annotations

from datetime import UTC, datetime
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

    def confirmar(self, pago_id: UUID, usuario_id: UUID) -> Pago:
        """Confirma un pago simulado imputando el ingreso a `usuario_id` (R4).

        `usuario_id` es obligatorio: `movimientos_caja.usuario_id` es `NOT NULL`
        y R4 exige usuario responsable en todo cobro (deuda de C-17).
        """
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
                usuario_id=usuario_id,
            )
            self.db.add(mov)
            self.db.flush()  # asigna mov.id antes de referenciarlo
            p.movimiento_id = mov.id
            p.estado = "aprobado"
            p.confirmado_en = datetime.now(UTC)
        else:
            p.estado = "rechazado"
        self.db.commit()
        self.db.refresh(p)
        return p

    def listar(self) -> list[Pago]:
        return self.db.query(Pago).all()