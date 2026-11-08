"""Servicio de caja (C-08 + C-12): libro append-only, cierre, cuenta corriente y ajustes."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.timezone import ahora, fin_dia, inicio_dia
from app.modules.admin.models import Usuario
from app.modules.agenda.models import Turno
from app.modules.caja.models import (
    MEDIOS_PAGO,
    AjusteCaja,
    CierreCaja,
    CuentaCorrientePaciente,
    MovimientoCaja,
)
from app.modules.caja.schemas import (
    AjusteCreate,
    CierreCreate,
    MovimientoCreate,
    ResumenDiarioOut,
)
from app.modules.clinica.models import Paciente

_CERO = Decimal("0.00")
_ROLES_AJUSTE_CIERRE = ("admin",)


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

    def _dia_esta_cerrado(self, fecha: date) -> bool:
        """Devuelve True si el día calendario tiene un cierre aprobado (bloqueo de período)."""
        cierre = self.db.scalar(
            select(CierreCaja).where(
                CierreCaja.fecha_dia == fecha,
                CierreCaja.estado == "cerrado",
            )
        )
        return cierre is not None

    def registrar(self, datos: MovimientoCreate, usuario_id: UUID) -> MovimientoCaja:
        """Registra un movimiento. Rechaza con 409 si el día del movimiento está cerrado."""
        fecha_movimiento = ahora().date()
        if self._dia_esta_cerrado(fecha_movimiento):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se pueden registrar movimientos en un día cerrado",
            )
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
        self._recalcular_cuenta_corriente_por_turno(datos.turno_id)
        return movimiento

    def _recalcular_cuenta_corriente_por_turno(self, turno_id: UUID | None) -> None:
        """Recalcula la cuenta corriente del paciente dueño del turno (D2: caché derivada)."""
        if turno_id is None:
            return
        turno = self.db.scalar(select(Turno).where(Turno.id == turno_id))
        if turno is None:
            return
        CuentaCorrienteService(self.db).recalcular(turno.paciente_id)

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


class CierreService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _require_admin(self, usuario_id: UUID) -> Usuario:
        usuario = self.db.scalar(select(Usuario).where(Usuario.id == usuario_id))
        if usuario is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
            )
        if usuario.rol != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Rol insuficiente"
            )
        return usuario

    def cerrar(self, datos: CierreCreate, usuario_id: UUID) -> CierreCaja:
        """Cierra un día calendario. Solo admin. 409 si el día ya está cerrado."""
        self._require_admin(usuario_id)
        dia = datos.fecha_dia or ahora().date()

        # 409: día ya cerrado
        existente = self.db.scalar(
            select(CierreCaja).where(CierreCaja.fecha_dia == dia)
        )
        if existente is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El día ya tiene un cierre",
            )

        # Calcular balance desde el libro del día (zona ART)
        movimientos = self.db.scalars(
            select(MovimientoCaja).where(
                MovimientoCaja.fecha >= inicio_dia(dia),
                MovimientoCaja.fecha < fin_dia(dia),
            )
        ).all()
        total_ingresos = sum(
            (m.monto for m in movimientos if m.tipo == "ingreso"), _CERO
        )
        total_egresos = sum(
            (m.monto for m in movimientos if m.tipo == "egreso"), _CERO
        )

        cierre = CierreCaja(
            fecha_dia=dia,
            estado="cerrado",
            balance=total_ingresos - total_egresos,
            total_ingresos=total_ingresos,
            total_egresos=total_egresos,
            aprobado_por=usuario_id,
            aprobado_en=ahora(),
        )
        self.db.add(cierre)
        self.db.commit()
        self.db.refresh(cierre)
        return cierre

    def listar(self) -> list[CierreCaja]:
        stmt = select(CierreCaja).order_by(CierreCaja.fecha_dia.desc())
        return list(self.db.scalars(stmt))


class CuentaCorrienteService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _paciente_vigente(self, paciente_id: UUID) -> Paciente:
        paciente = self.db.scalar(
            select(Paciente).where(Paciente.id == paciente_id, Paciente.deleted_at.is_(None))
        )
        if paciente is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado"
            )
        return paciente

    def saldo(self, paciente_id: UUID) -> Decimal:
        """Saldo derivado: suma(ingresos) - suma(egresos) de movimientos vinculados a turnos del paciente."""
        self._paciente_vigente(paciente_id)
        ingresos = self.db.scalar(
            select(func.coalesce(func.sum(MovimientoCaja.monto), _CERO))
            .join(Turno, MovimientoCaja.turno_id == Turno.id)
            .where(Turno.paciente_id == paciente_id)
            .where(MovimientoCaja.tipo == "ingreso")
        )
        egresos = self.db.scalar(
            select(func.coalesce(func.sum(MovimientoCaja.monto), _CERO))
            .join(Turno, MovimientoCaja.turno_id == Turno.id)
            .where(Turno.paciente_id == paciente_id)
            .where(MovimientoCaja.tipo == "egreso")
        )
        return (ingresos or _CERO) - (egresos or _CERO)

    def detalle(self, paciente_id: UUID) -> list[MovimientoCaja]:
        """Detalle de movimientos vinculados a turnos del paciente."""
        self._paciente_vigente(paciente_id)
        stmt = (
            select(MovimientoCaja)
            .join(Turno, MovimientoCaja.turno_id == Turno.id)
            .where(Turno.paciente_id == paciente_id)
            .order_by(MovimientoCaja.fecha.desc())
        )
        return list(self.db.scalars(stmt))

    def recalcular(self, paciente_id: UUID) -> None:
        """Recalcula y persiste el saldo en cuentas_corrientes_paciente (caché derivada, D2)."""
        saldo = self.saldo(paciente_id)
        cuenta = self.db.scalar(
            select(CuentaCorrientePaciente).where(
                CuentaCorrientePaciente.paciente_id == paciente_id
            )
        )
        ahora_ts = ahora()
        if cuenta is None:
            cuenta = CuentaCorrientePaciente(
                paciente_id=paciente_id,
                saldo=saldo,
                actualizado_en=ahora_ts,
            )
            self.db.add(cuenta)
        else:
            cuenta.saldo = saldo
            cuenta.actualizado_en = ahora_ts
        self.db.commit()


class AjusteService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _require_admin(self, usuario_id: UUID) -> Usuario:
        usuario = self.db.scalar(select(Usuario).where(Usuario.id == usuario_id))
        if usuario is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
            )
        if usuario.rol != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Rol insuficiente"
            )
        return usuario

    def registrar(self, datos: AjusteCreate, usuario_id: UUID) -> AjusteCaja:
        """Registra un ajuste auditado: contra-asiento + fila en ajustes_caja. Solo admin."""
        self._require_admin(usuario_id)

        # Verificar que el movimiento corregido existe
        movimiento_corregido = self.db.scalar(
            select(MovimientoCaja).where(MovimientoCaja.id == datos.movimiento_corregido_id)
        )
        if movimiento_corregido is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movimiento corregido no encontrado",
            )

        # Crear contra-asiento (movimiento nuevo, nunca tocar el original)
        contra_asiento = MovimientoCaja(
            tipo=datos.tipo,
            medio_pago=datos.medio_pago,
            monto=datos.monto,
            concepto=datos.concepto,
            turno_id=datos.turno_id,
            usuario_id=usuario_id,
        )
        self.db.add(contra_asiento)
        self.db.flush()  # obtener id sin commit todavía

        # Crear fila de ajuste vinculando original y contra-asiento
        ajuste = AjusteCaja(
            movimiento_corregido_id=datos.movimiento_corregido_id,
            movimiento_ajuste_id=contra_asiento.id,
            motivo=datos.motivo,
            fecha=ahora(),
            usuario_aprobador_id=usuario_id,
        )
        self.db.add(ajuste)
        self.db.commit()
        self.db.refresh(ajuste)
        # Recalcular cuenta corriente del paciente del movimiento corregido si tiene turno
        if movimiento_corregido.turno_id is not None:
            turno = self.db.scalar(select(Turno).where(Turno.id == movimiento_corregido.turno_id))
            if turno is not None:
                CuentaCorrienteService(self.db).recalcular(turno.paciente_id)
        return ajuste
