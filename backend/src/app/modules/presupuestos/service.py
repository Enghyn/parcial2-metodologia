"""Servicio de presupuestos (C-16)."""
from __future__ import annotations

from datetime import UTC
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.audit.service import registrar_auditoria
from app.modules.presupuestos.models import ItemPresupuesto, Presupuesto
from app.modules.presupuestos.schemas import PresupuestoCreate


class PresupuestoService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def crear(self, datos: PresupuestoCreate, *, usuario_id=None) -> Presupuesto:
        p = Presupuesto(paciente_id=datos.paciente_id, estado="borrador")
        self.db.add(p)
        self.db.flush()
        total = 0.0
        for it in datos.items:
            item = ItemPresupuesto(
                presupuesto_id=p.id,
                descripcion=it.descripcion,
                cantidad=it.cantidad,
                arancel=it.arancel,
                copago=it.copago,
            )
            self.db.add(item)
            total += it.arancel * it.cantidad - it.copago
        p.total = total
        self.db.flush()
        registrar_auditoria(
            self.db,
            usuario_id=usuario_id,
            accion="crear",
            recurso="presupuesto",
            recurso_id=p.id,
            diff={"paciente_id": str(datos.paciente_id), "total": total, "items": len(datos.items)},
        )
        self.db.commit()
        self.db.refresh(p)
        return p

    def aprobar(self, token: UUID) -> Presupuesto:
        p = self.db.query(Presupuesto).filter(Presupuesto.token_publico == token).first()
        if p is None:
            raise ValueError("not_found")
        p.estado = "aprobado"
        from datetime import datetime

        p.aprobado_en = datetime.now(UTC)
        self.db.flush()
        registrar_auditoria(
            self.db,
            usuario_id=None,
            accion="aprobar",
            recurso="presupuesto",
            recurso_id=p.id,
            diff={"estado": "aprobado"},
        )
        self.db.commit()
        self.db.refresh(p)
        return p

    def listar(self) -> list[Presupuesto]:
        return self.db.query(Presupuesto).all()