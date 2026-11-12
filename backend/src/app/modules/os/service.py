"""Servicio de OS, convenios y afiliación (C-13a)."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.os.models import Convenio, ObraSocial, PacienteObraSocial
from app.modules.os.schemas import AfiliacionCreate, ConvenioCreate, ObraSocialCreate


class ObraSocialService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def listar(self) -> list[ObraSocial]:
        return self.db.query(ObraSocial).order_by(ObraSocial.nombre).all()

    def crear(self, datos: ObraSocialCreate) -> ObraSocial:
        existente = self.db.query(ObraSocial).filter(ObraSocial.nombre == datos.nombre).first()
        if existente:
            raise ValueError("nombre_duplicado")
        os_ = ObraSocial(nombre=datos.nombre, codigo=datos.codigo, activo=datos.activo)
        self.db.add(os_)
        self.db.commit()
        self.db.refresh(os_)
        return os_


class ConvenioService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def listar(self, obra_social_id: UUID | None = None) -> list[Convenio]:
        q = self.db.query(Convenio)
        if obra_social_id is not None:
            q = q.filter(Convenio.obra_social_id == obra_social_id)
        return q.order_by(Convenio.nombre).all()

    def crear(self, datos: ConvenioCreate) -> Convenio:
        c = Convenio(
            obra_social_id=datos.obra_social_id,
            nombre=datos.nombre,
            vigente_desde=datos.vigente_desde,
            vigente_hasta=datos.vigente_hasta,
            descuento_global=datos.descuento_global,
            activo=datos.activo,
        )
        self.db.add(c)
        self.db.commit()
        self.db.refresh(c)
        return c


class AfiliacionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def crear(self, datos: AfiliacionCreate) -> PacienteObraSocial:
        a = PacienteObraSocial(
            paciente_id=datos.paciente_id,
            obra_social_id=datos.obra_social_id,
            convenio_id=datos.convenio_id,
            nro_afiliado=datos.nro_afiliado,
            vigente_desde=datos.vigente_desde,
            vigente_hasta=datos.vigente_hasta,
        )
        self.db.add(a)
        self.db.commit()
        self.db.refresh(a)
        return a

    def vigente(self, paciente_id: UUID) -> PacienteObraSocial | None:
        from datetime import date

        hoy = date.today()
        return (
            self.db.query(PacienteObraSocial)
            .filter(PacienteObraSocial.paciente_id == paciente_id)
            .filter(PacienteObraSocial.vigente_desde <= hoy)
            .filter(
                (PacienteObraSocial.vigente_hasta.is_(None))
                | (PacienteObraSocial.vigente_hasta >= hoy)
            )
            .first()
        )