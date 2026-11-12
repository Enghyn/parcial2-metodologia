"""Servicio de comprobante (C-13b)."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.comprobante.models import Comprobante
from app.modules.comprobante.schemas import ComprobanteCreate


class Facturador:
    def emitir(self, db: Session, datos: ComprobanteCreate, usuario_id: UUID) -> Comprobante:
        raise NotImplementedError


class FacturadorManual(Facturador):
    def emitir(self, db: Session, datos: ComprobanteCreate, usuario_id: UUID) -> Comprobante:
        comp = Comprobante(
            numero=datos.numero,
            movimiento_id=datos.movimiento_id,
            presupuesto_id=datos.presupuesto_id,
            estado="emitido",
            emitido_por=usuario_id,
            emitido_en=datetime.now(timezone.utc),
        )
        db.add(comp)
        db.commit()
        db.refresh(comp)
        return comp


class ComprobanteService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.facturador = FacturadorManual()

    def crear(self, datos: ComprobanteCreate, usuario_id: UUID) -> Comprobante:
        return self.facturador.emitir(self.db, datos, usuario_id)

    def anular(self, comprobante_id: UUID) -> Comprobante:
        comp = self.db.query(Comprobante).filter(Comprobante.id == comprobante_id).first()
        if comp is None:
            raise ValueError("not_found")
        comp.estado = "anulado"
        comp.anulado_en = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(comp)
        return comp