"""Servicio de lista de espera (C-15)."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.lista_espera.models import ListaEspera
from app.modules.lista_espera.schemas import ListaEsperaCreate


class ListaEsperaService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def crear(self, datos: ListaEsperaCreate) -> ListaEspera:
        le = ListaEspera(
            paciente_id=datos.paciente_id,
            profesional_id=datos.profesional_id,
            sillon_id=datos.sillon_id,
            fecha_preferida=datos.fecha_preferida,
            estado="pendiente",
        )
        self.db.add(le)
        self.db.commit()
        self.db.refresh(le)
        return le

    def listar(self) -> list[ListaEspera]:
        return self.db.query(ListaEspera).order_by(ListaEspera.created_at).all()

    def ofrecer(self, le_id: UUID, expira_en: datetime) -> ListaEspera:
        le = self.db.query(ListaEspera).filter(ListaEspera.id == le_id).first()
        if le is None:
            raise ValueError("not_found")
        le.estado = "ofrecido"
        le.ofrecido_en = datetime.now(UTC)
        le.expira_en = expira_en
        self.db.commit()
        self.db.refresh(le)
        return le