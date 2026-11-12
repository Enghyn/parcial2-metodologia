"""Servicio de notificaciones (C-14)."""
from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.notificaciones.models import Notificacion
from app.modules.notificaciones.schemas import NotificacionCreate


class Notificador:
    def enviar(self, db: Session, datos: NotificacionCreate) -> Notificacion:
        raise NotImplementedError


class NotificadorSimulado(Notificador):
    PLANTILLAS = {
        "confirmacion": "Turno confirmado",
        "recordatorio_24h": "Recordatorio 24h",
        "recordatorio_2h": "Recordatorio 2h",
        "lista_espera": "Lista de espera",
    }

    def link_wa(self, telefono: str, mensaje: str) -> str:
        return f"https://wa.me/{telefono}?text={quote(mensaje)}"

    def enviar(self, db: Session, datos: NotificacionCreate) -> Notificacion:
        n = Notificacion(
            turno_id=datos.turno_id,
            plantilla=datos.plantilla,
            destinatario=datos.destinatario,
            estado="enviado",
            enviado_en=datetime.now(timezone.utc),
        )
        db.add(n)
        db.commit()
        db.refresh(n)
        return n


class NotificacionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.notificador = NotificadorSimulado()

    def crear(self, datos: NotificacionCreate) -> Notificacion:
        return self.notificador.enviar(self.db, datos)

    def listar(self) -> list[Notificacion]:
        return self.db.query(Notificacion).order_by(Notificacion.created_at.desc()).all()