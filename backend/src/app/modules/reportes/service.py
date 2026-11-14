"""Servicio de reportes de gestion (C-21): solo lectura sobre tablas existentes.

Consulta `Turno`, `MovimientoCaja`, `Sillon`, `Profesional`, `Paciente`,
`Bloqueo`, `ObraSocial`, `Convenio` y `PacienteObraSocial`. No crea ni modifica
tablas; no hay migracion (R5). Mono-consultorio, sin `tenant_id` (R2).
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.timezone import ahora, fin_dia, inicio_dia
from app.modules.agenda.models import Bloqueo, Profesional, Sillon, Turno
from app.modules.caja.models import MEDIOS_PAGO, MovimientoCaja
from app.modules.clinica.models import Paciente
from app.modules.os.models import Convenio, ObraSocial, PacienteObraSocial
from app.modules.reportes.csv import render_csv
from app.modules.reportes.schemas import (
    AusentismoOut,
    AusentismoTurnoOut,
    FacturacionMedioOut,
    FacturacionOSOut,
    FacturacionOut,
    OcupacionOut,
    OcupacionRecursoOut,
)

_CERO = Decimal("0.00")
_DIAS_DEFAULT = 30
_ESTADOS_DENOMINADOR = ("reservado", "confirmado", "presente", "atendido")
_ESTADOS_AUSENTE = ("cancelado", "ausente")


class ReportesService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _rango(self, desde: date | None, hasta: date | None) -> tuple[date, date]:
        """Resuelve el rango con default de ultimos 30 dias calendario ART."""
        hoy = ahora().date()
        dia_hasta = hasta or hoy
        dia_desde = desde or (dia_hasta - timedelta(days=_DIAS_DEFAULT))
        return dia_desde, dia_hasta

    def _validar_rango(self, desde: date, hasta: date) -> None:
        if desde > hasta:
            raise ValueError("desde no puede ser posterior a hasta")

    # ------------------------------------------------------------------ ocupacion

    def reporte_ocupacion(
        self,
        desde: date | None,
        hasta: date | None,
        profesional_id: UUID | None = None,
        sillon_id: UUID | None = None,
    ) -> OcupacionOut:
        dia_desde, dia_hasta = self._rango(desde, hasta)
        self._validar_rango(dia_desde, dia_hasta)
        ini = inicio_dia(dia_desde)
        fin = fin_dia(dia_hasta)

        turnos = list(
            self.db.scalars(
                select(Turno).where(
                    Turno.deleted_at.is_(None),
                    Turno.inicio >= ini,
                    Turno.inicio < fin,
                )
            )
        )
        if profesional_id is not None:
            turnos = [t for t in turnos if t.profesional_id == profesional_id]
        if sillon_id is not None:
            turnos = [t for t in turnos if t.sillon_id == sillon_id]

        # Solo se listan recursos que tienen turnos en el rango: lista vacia
        # cuando no hay turnos, segun el escenario de especificacion.
        sillones_con_turnos = {t.sillon_id for t in turnos}
        profesionales_con_turnos = {t.profesional_id for t in turnos}

        def conteos(filas: list[Turno]) -> dict[str, int]:
            c = {estado: 0 for estado in _ESTADOS_DENOMINADOR + ("cancelado",)}
            for t in filas:
                if t.estado in c:
                    c[t.estado] += 1
            return c

        def tasa(c: dict[str, int]) -> float:
            den = sum(c[e] for e in _ESTADOS_DENOMINADOR)
            return round(c["atendido"] / den, 4) if den else 0.0

        # horas bloqueadas: una consulta, sin N+1
        bloqueos = list(
            self.db.scalars(
                select(Bloqueo).where(Bloqueo.hasta > ini, Bloqueo.desde < fin)
            )
        )
        hb_por_recurso: dict[tuple[UUID | None, UUID | None], timedelta] = defaultdict(timedelta)
        for b in bloqueos:
            ini_solap = max(b.desde, ini)
            fin_solap = min(b.hasta, fin)
            if fin_solap > ini_solap:
                hb_por_recurso[(b.sillon_id, b.profesional_id)] += fin_solap - ini_solap

        def horas(sillon_id: UUID | None, profesional_id: UUID | None) -> float:
            td = hb_por_recurso.get((sillon_id, profesional_id), timedelta())
            return round(td.total_seconds() / 3600.0, 2)

        filas_sillon: list[OcupacionRecursoOut] = []
        for s in self.db.scalars(select(Sillon).where(Sillon.deleted_at.is_(None))):
            if s.id not in sillones_con_turnos:
                continue
            if sillon_id is not None and s.id != sillon_id:
                continue
            c = conteos([t for t in turnos if t.sillon_id == s.id])
            filas_sillon.append(
                OcupacionRecursoOut(
                    id=s.id,
                    nombre=s.nombre,
                    reservado=c["reservado"],
                    confirmado=c["confirmado"],
                    presente=c["presente"],
                    atendido=c["atendido"],
                    cancelado=c["cancelado"],
                    tasa_ocupacion=tasa(c),
                    horas_bloqueadas=horas(s.id, None),
                )
            )

        filas_profesional: list[OcupacionRecursoOut] = []
        for p in self.db.scalars(select(Profesional).where(Profesional.deleted_at.is_(None))):
            if p.id not in profesionales_con_turnos:
                continue
            if profesional_id is not None and p.id != profesional_id:
                continue
            c = conteos([t for t in turnos if t.profesional_id == p.id])
            filas_profesional.append(
                OcupacionRecursoOut(
                    id=p.id,
                    nombre=p.nombre,
                    reservado=c["reservado"],
                    confirmado=c["confirmado"],
                    presente=c["presente"],
                    atendido=c["atendido"],
                    cancelado=c["cancelado"],
                    tasa_ocupacion=tasa(c),
                    horas_bloqueadas=horas(None, p.id),
                )
            )

        return OcupacionOut(
            desde=dia_desde,
            hasta=dia_hasta,
            sillones=filas_sillon,
            profesionales=filas_profesional,
        )

    # ---------------------------------------------------------------- facturacion

    def reporte_facturacion(
        self, desde: date | None, hasta: date | None
    ) -> FacturacionOut:
        dia_desde, dia_hasta = self._rango(desde, hasta)
        self._validar_rango(dia_desde, dia_hasta)
        ini = inicio_dia(dia_desde)
        fin = fin_dia(dia_hasta)

        movimientos = list(
            self.db.scalars(
                select(MovimientoCaja).where(
                    MovimientoCaja.tipo == "ingreso",
                    MovimientoCaja.fecha >= ini,
                    MovimientoCaja.fecha < fin,
                )
            )
        )

        por_medio: dict[str, Decimal] = {}
        for mov in movimientos:
            por_medio[mov.medio_pago] = por_medio.get(mov.medio_pago, _CERO) + mov.monto
        total_ingresos = sum(por_medio.values(), _CERO)

        # Desglose por obra social: una consulta con joins, sin N+1.
        filas_os = list(
            self.db.execute(
                select(
                    MovimientoCaja.id,
                    MovimientoCaja.monto,
                    ObraSocial.nombre,
                    Convenio.descuento_global,
                )
                .join(Turno, MovimientoCaja.turno_id == Turno.id)
                .join(Paciente, Turno.paciente_id == Paciente.id)
                .join(PacienteObraSocial, PacienteObraSocial.paciente_id == Paciente.id)
                .join(ObraSocial, ObraSocial.id == PacienteObraSocial.obra_social_id)
                .outerjoin(Convenio, Convenio.id == PacienteObraSocial.convenio_id)
                .where(
                    MovimientoCaja.tipo == "ingreso",
                    MovimientoCaja.fecha >= ini,
                    MovimientoCaja.fecha < fin,
                    Paciente.deleted_at.is_(None),
                    PacienteObraSocial.vigente_desde <= dia_hasta,
                    (PacienteObraSocial.vigente_hasta.is_(None))
                    | (PacienteObraSocial.vigente_hasta >= dia_desde),
                    ObraSocial.activo.is_(True),
                )
            )
        )

        os_por_movimiento: dict[UUID, tuple[Decimal, str, Decimal | None]] = {}
        for mov_id, monto, os_nombre, descuento in filas_os:
            if mov_id not in os_por_movimiento:
                os_por_movimiento[mov_id] = (monto, os_nombre, descuento)

        por_os: dict[str, dict[str, Decimal]] = defaultdict(
            lambda: {"monto_os": _CERO, "copago": _CERO}
        )
        for mov_id, (monto, os_nombre, descuento) in os_por_movimiento.items():
            desc = descuento or Decimal(0)
            monto_os = (monto * desc / Decimal(100)).quantize(Decimal("0.01"))
            copago = (monto - monto_os).quantize(Decimal("0.01"))
            por_os[os_nombre]["monto_os"] += monto_os
            por_os[os_nombre]["copago"] += copago

        # Movimientos sin turno o sin afiliacion vigente -> "sin OS" (100% paciente).
        for mov in movimientos:
            if mov.id not in os_por_movimiento:
                por_os["sin OS"]["copago"] += mov.monto

        filas_os_out = [
            FacturacionOSOut(
                obra_social=nombre,
                monto_os=valores["monto_os"],
                copago_paciente=valores["copago"],
                total_paciente=valores["monto_os"] + valores["copago"],
            )
            for nombre, valores in por_os.items()
        ]

        return FacturacionOut(
            desde=dia_desde,
            hasta=dia_hasta,
            por_medio_pago=[
                FacturacionMedioOut(medio_pago=medio, total=por_medio[medio])
                for medio in MEDIOS_PAGO
                if medio in por_medio
            ],
            total_ingresos=total_ingresos,
            balance_neto=total_ingresos,
            por_obra_social=filas_os_out,
        )

    # ---------------------------------------------------------------- ausentismo

    def reporte_ausentismo(
        self, desde: date | None, hasta: date | None
    ) -> AusentismoOut:
        dia_desde, dia_hasta = self._rango(desde, hasta)
        self._validar_rango(dia_desde, dia_hasta)
        ini = inicio_dia(dia_desde)
        fin = fin_dia(dia_hasta)

        turnos = list(
            self.db.scalars(
                select(Turno).where(
                    Turno.deleted_at.is_(None),
                    Turno.inicio >= ini,
                    Turno.inicio < fin,
                )
            )
        )

        cancelados = sum(1 for t in turnos if t.estado == "cancelado")
        no_presentados = sum(1 for t in turnos if t.estado == "ausente")
        total_turnos = len(turnos)

        # Recuperados (heuristica D5): paciente con varios turnos en el rango =>
        # todos excepto el primero cuentan como reagendados.
        por_paciente: dict[UUID, int] = defaultdict(int)
        for t in turnos:
            por_paciente[t.paciente_id] += 1
        recuperados = sum(max(0, n - 1) for n in por_paciente.values())

        den = total_turnos
        tasa = round((cancelados + no_presentados) / den, 4) if den else 0.0

        return AusentismoOut(
            desde=dia_desde,
            hasta=dia_hasta,
            cancelados=cancelados,
            no_presentados=no_presentados,
            recuperados=recuperados,
            tasa_ausentismo=tasa,
            total_turnos=total_turnos,
        )

    def turnos_ausentes(
        self, desde: date | None, hasta: date | None
    ) -> list[AusentismoTurnoOut]:
        """Turnos cancelados / no presentados en el rango (detalle para CSV)."""
        dia_desde, dia_hasta = self._rango(desde, hasta)
        self._validar_rango(dia_desde, dia_hasta)
        ini = inicio_dia(dia_desde)
        fin = fin_dia(dia_hasta)

        turnos = list(
            self.db.scalars(
                select(Turno).where(
                    Turno.deleted_at.is_(None),
                    Turno.estado.in_(_ESTADOS_AUSENTE),
                    Turno.inicio >= ini,
                    Turno.inicio < fin,
                )
            )
        )
        return [
            AusentismoTurnoOut(
                turno_id=t.id,
                inicio=t.inicio,
                estado=t.estado,
                profesional_id=t.profesional_id,
                sillon_id=t.sillon_id,
            )
            for t in turnos
        ]

    # ------------------------------------------------------------------ export csv

    def exportar_ocupacion_csv(
        self,
        desde: date | None,
        hasta: date | None,
        profesional_id: UUID | None = None,
        sillon_id: UUID | None = None,
    ) -> tuple[bytes, str]:
        resultado = self.reporte_ocupacion(desde, hasta, profesional_id, sillon_id)
        columnas = [
            "recurso",
            "id",
            "nombre",
            "reservado",
            "confirmado",
            "presente",
            "atendido",
            "cancelado",
            "tasa_ocupacion",
            "horas_bloqueadas",
        ]
        filas: list[list[object]] = []
        for s in resultado.sillones:
            filas.append(
                [
                    "sillon",
                    str(s.id),
                    s.nombre,
                    s.reservado,
                    s.confirmado,
                    s.presente,
                    s.atendido,
                    s.cancelado,
                    s.tasa_ocupacion,
                    s.horas_bloqueadas,
                ]
            )
        for p in resultado.profesionales:
            filas.append(
                [
                    "profesional",
                    str(p.id),
                    p.nombre,
                    p.reservado,
                    p.confirmado,
                    p.presente,
                    p.atendido,
                    p.cancelado,
                    p.tasa_ocupacion,
                    p.horas_bloqueadas,
                ]
            )
        nombre = f"ocupacion-{resultado.desde.isoformat()}_{resultado.hasta.isoformat()}.csv"
        return render_csv(columnas, filas), nombre

    def exportar_facturacion_csv(
        self, desde: date | None, hasta: date | None
    ) -> tuple[bytes, str]:
        resultado = self.reporte_facturacion(desde, hasta)
        columnas = ["medio_pago", "total_ingresos"]
        filas: list[list[object]] = [
            [medio.medio_pago, medio.total] for medio in resultado.por_medio_pago
        ]
        filas.append(["TOTAL", resultado.total_ingresos])
        nombre = f"facturacion-{resultado.desde.isoformat()}_{resultado.hasta.isoformat()}.csv"
        return render_csv(columnas, filas), nombre

    def exportar_ausentismo_csv(
        self, desde: date | None, hasta: date | None
    ) -> tuple[bytes, str]:
        resumen = self.reporte_ausentismo(desde, hasta)
        turnos = self.turnos_ausentes(desde, hasta)
        columnas = ["turno_id", "inicio", "estado", "profesional_id", "sillon_id"]
        filas: list[list[object]] = [
            [t.turno_id, t.inicio, t.estado, t.profesional_id, t.sillon_id]
            for t in turnos
        ]
        filas.append(["TOTAL", resumen.cancelados + resumen.no_presentados, "", "", ""])
        nombre = f"ausentismo-{resumen.desde.isoformat()}_{resumen.hasta.isoformat()}.csv"
        return render_csv(columnas, filas), nombre


__all__ = ["ReportesService"]
