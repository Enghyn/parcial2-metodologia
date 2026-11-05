// Acción rápida de cambio de estado.
import type { ReactElement } from "react";
import type { EstadoTurno } from "../../shared/api/agenda";

interface EstadoTurnoMenuProps {
  turnoId: string;
  rol: string;
  estadoActual: EstadoTurno;
  onCambiarEstado: (id: string, estado: EstadoTurno) => void;
}

const OPCIONES: EstadoTurno[] = ["confirmado", "presente", "cancelado", "ausente"];

export function EstadoTurnoMenu({
  turnoId,
  rol,
  estadoActual,
  onCambiarEstado,
}: EstadoTurnoMenuProps): ReactElement {
  const puedeConfirmar = rol === "admin" || rol === "recepcion";
  return (
    <div className="mt-2 flex flex-wrap gap-1">
      {OPCIONES.map((estado) => {
        if (estado === "confirmado" && !puedeConfirmar) return null;
        if (estado === estadoActual) return null;
        return (
          <button
            key={estado}
            type="button"
            onClick={() => onCambiarEstado(turnoId, estado)}
            className="rounded border border-border px-2 py-0.5 text-[10px] hover:bg-foreground/5"
          >
            {estado}
          </button>
        );
      })}
    </div>
  );
}