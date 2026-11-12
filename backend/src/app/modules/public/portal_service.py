"""Servicio del portal público de presupuestos y pagos (C-18, D1/D3/D4/D5).

Reusa los tokens opacos existentes (`Presupuesto.token_publico`, D2) y los
servicios de presupuestos/pagos/caja. R9: los métodos públicos solo reciben un
token opaco y devuelven DTOs mínimos; un token inexistente se traduce siempre a
404 genérico, sin distinguir "no existe" de "no corresponde".
"""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.timezone import ahora
from app.modules.admin.models import Usuario
from app.modules.caja.models import MovimientoCaja
from app.modules.pagos.models import IntentoPago, Pago
from app.modules.pagos.service import CobradorSimulado
from app.modules.presupuestos.models import ItemPresupuesto, Presupuesto
from app.modules.public.schemas import (
    ConfirmarPublicoIn,
    ItemPresupuestoPublicoOut,
    PagoPublicoOut,
    PresupuestoPublicoOut,
)

# D5: solo se firma/aprueba/rechaza un presupuesto recién enviado.
_ESTADO_FIRMABLE = "enviado"
_ESTADO_APROBADO = "aprobado"

# D4: el canal portal es anónimo, así que el cobro se imputa a un usuario de
# sistema configurable. Concepto y medio fijos para trazabilidad del origen.
_CONCEPTO_PAGO_PORTAL = "Pago simulado (portal)"
_MEDIO_PAGO_PORTAL = "otro"


class PortalPublicoService:
    """Orquesta la vista pública del presupuesto y la confirmación del pago."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.cobrador = CobradorSimulado()

    # --- Resolución por token opaco (R9) ---

    def _presupuesto_por_token(
        self, token: UUID, *, for_update: bool = False
    ) -> Presupuesto:
        stmt = select(Presupuesto).where(Presupuesto.token_publico == token)
        if for_update:
            # D3: reclamo atómico; serializa confirmaciones concurrentes.
            stmt = stmt.with_for_update()
        presupuesto = self.db.scalar(stmt)
        if presupuesto is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Presupuesto no encontrado",
            )
        return presupuesto

    def _items_publicos(self, presupuesto_id: UUID) -> list[ItemPresupuestoPublicoOut]:
        items = self.db.scalars(
            select(ItemPresupuesto)
            .where(ItemPresupuesto.presupuesto_id == presupuesto_id)
            .order_by(ItemPresupuesto.created_at, ItemPresupuesto.descripcion)
        )
        return [
            ItemPresupuestoPublicoOut(
                descripcion=item.descripcion,
                cantidad=item.cantidad,
                arancel=float(item.arancel),
                copago=float(item.copago),
            )
            for item in items
        ]

    def _to_publico(self, presupuesto: Presupuesto) -> PresupuestoPublicoOut:
        return PresupuestoPublicoOut(
            estado=presupuesto.estado,
            total=float(presupuesto.total),
            items=self._items_publicos(presupuesto.id),
        )

    # --- Tarea 2.1: lectura y firma simple ---

    def obtener_presupuesto_publico(self, token: UUID) -> PresupuestoPublicoOut:
        return self._to_publico(self._presupuesto_por_token(token))

    def aprobar(self, token: UUID, firma: str) -> PresupuestoPublicoOut:
        """Aprueba un presupuesto `enviado`; repetir sobre `aprobado` es idempotente."""
        presupuesto = self._presupuesto_por_token(token)
        if presupuesto.estado == _ESTADO_APROBADO:
            return self._to_publico(presupuesto)
        if presupuesto.estado != _ESTADO_FIRMABLE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"No se puede aprobar un presupuesto en estado {presupuesto.estado}",
            )
        presupuesto.estado = _ESTADO_APROBADO
        presupuesto.aprobado_en = ahora()
        self.db.commit()
        self.db.refresh(presupuesto)
        return self._to_publico(presupuesto)

    def rechazar(self, token: UUID, motivo: str | None) -> PresupuestoPublicoOut:
        """Rechaza un presupuesto `enviado`; otra transición es 409 (D5)."""
        presupuesto = self._presupuesto_por_token(token)
        if presupuesto.estado != _ESTADO_FIRMABLE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"No se puede rechazar un presupuesto en estado {presupuesto.estado}",
            )
        presupuesto.estado = "rechazado"
        self.db.commit()
        self.db.refresh(presupuesto)
        return self._to_publico(presupuesto)

    # --- Tarea 2.2: pago simulado del portal (D3/D4) ---

    def _pago_por_estado(self, presupuesto_id: UUID, estado: str) -> Pago | None:
        return self.db.scalar(
            select(Pago)
            .where(Pago.presupuesto_id == presupuesto_id, Pago.estado == estado)
            .order_by(Pago.created_at.desc())
        )

    def _usuario_portal(self) -> Usuario:
        """D4/R4: usuario responsable del cobro anónimo del portal."""
        email = get_settings().portal_usuario_email.strip().lower()
        usuario = self.db.scalar(
            select(Usuario).where(Usuario.email == email, Usuario.activo.is_(True))
        )
        if usuario is None:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se pudo procesar el pago en este momento",
            )
        return usuario

    def _pago_to_publico(self, pago: Pago) -> PagoPublicoOut:
        return PagoPublicoOut(
            estado=pago.estado,
            monto=float(pago.monto),
            confirmado_en=pago.confirmado_en,
        )

    def obtener_pago_publico(self, token: UUID) -> PagoPublicoOut:
        """Vista pública del pago del presupuesto; solo si está `aprobado` (D5).

        Si todavía no existe una fila `Pago`, devuelve un estado `pendiente`
        sintetizado por el total adeudado sin crear registros (solo lectura).
        """
        presupuesto = self._presupuesto_por_token(token)
        if presupuesto.estado != _ESTADO_APROBADO:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El presupuesto todavía no está listo para pagar",
            )
        pago = self._pago_por_estado(presupuesto.id, _ESTADO_APROBADO)
        if pago is None:
            pago = self._pago_por_estado(presupuesto.id, "pendiente")
        if pago is not None:
            return self._pago_to_publico(pago)
        return PagoPublicoOut(
            estado="pendiente",
            monto=float(presupuesto.total),
            confirmado_en=None,
        )

    def confirmar_pago_publico(self, token: UUID, datos: ConfirmarPublicoIn | None = None) -> PagoPublicoOut:
        """Confirma (idempotente) el pago simulado del presupuesto `aprobado` (D3).

        ``datos`` es opcional:
        - ``None`` o no enviado → comportamiento anterior (sin validación de body).
        - ``{}`` → válido, continúa normalmente.
        - body con campo no declarado → 422 (R1, extra="forbid").
        """
        presupuesto = self._presupuesto_por_token(token, for_update=True)
        if presupuesto.estado != _ESTADO_APROBADO:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El presupuesto todavía no está listo para pagar",
            )
        # D5/RN-CJ-01: presupuesto con total <= 0 no es cobrable
        if float(presupuesto.total) <= 0:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El presupuesto no tiene un monto cobrable",
            )
        aprobado = self._pago_por_estado(presupuesto.id, _ESTADO_APROBADO)
        if aprobado is not None:
            out = self._pago_to_publico(aprobado)
            self.db.rollback()  # libera el lock: no hay escrituras
            return out

        usuario = self._usuario_portal()
        pago = self._pago_por_estado(presupuesto.id, "pendiente")
        if pago is None:
            pago = Pago(
                presupuesto_id=presupuesto.id,
                monto=presupuesto.total,
                estado="pendiente",
            )
            self.db.add(pago)
            self.db.flush()

        resultado = self.cobrador.procesar(float(pago.monto))
        self.db.add(IntentoPago(pago_id=pago.id, resultado=resultado))
        if resultado == "aprobado":
            movimiento = MovimientoCaja(
                tipo="ingreso",
                medio_pago=_MEDIO_PAGO_PORTAL,
                monto=pago.monto,
                concepto=_CONCEPTO_PAGO_PORTAL,
                usuario_id=usuario.id,
            )
            self.db.add(movimiento)
            self.db.flush()
            pago.movimiento_id = movimiento.id
            pago.estado = _ESTADO_APROBADO
            pago.confirmado_en = datetime.now(UTC)
        else:
            pago.estado = "rechazado"
        self.db.commit()
        self.db.refresh(pago)
        return self._pago_to_publico(pago)


__all__ = ["PortalPublicoService"]
