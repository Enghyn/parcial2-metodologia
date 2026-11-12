"""Servicio de nomenclador (C-13a)."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.nomenclador.models import ConvenioPractica, NomencladorPractica
from app.modules.nomenclador.schemas import ConvenioPracticaCreate, PracticaCreate


class NomencladorService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def listar_practicas(self) -> list[NomencladorPractica]:
        return self.db.query(NomencladorPractica).order_by(NomencladorPractica.codigo).all()

    def crear_practica(self, datos: PracticaCreate) -> NomencladorPractica:
        p = NomencladorPractica(
            codigo=datos.codigo, descripcion=datos.descripcion, arancel_base=datos.arancel_base
        )
        self.db.add(p)
        self.db.commit()
        self.db.refresh(p)
        return p

    def crear_convenio_practica(self, datos: ConvenioPracticaCreate) -> ConvenioPractica:
        cp = ConvenioPractica(
            convenio_id=datos.convenio_id,
            practica_id=datos.practica_id,
            arancel_override=datos.arancel_override,
            copago_fijo=datos.copago_fijo,
            copago_porcentaje=datos.copago_porcentaje,
        )
        self.db.add(cp)
        self.db.commit()
        self.db.refresh(cp)
        return cp


def calcular_cobertura(arancel_base: float, convenio_practica: ConvenioPractica | None) -> dict:
    arancel = arancel_base
    if convenio_practica and convenio_practica.arancel_override is not None:
        arancel = float(convenio_practica.arancel_override)
    copago = 0.0
    if convenio_practica:
        if convenio_practica.copago_fijo is not None:
            copago = float(convenio_practica.copago_fijo)
        elif convenio_practica.copago_porcentaje is not None:
            copago = arancel * (float(convenio_practica.copago_porcentaje) / 100.0)
    monto_os = arancel - copago
    return {"arancel": arancel, "copago": copago, "monto_os": monto_os, "monto_paciente": copago}