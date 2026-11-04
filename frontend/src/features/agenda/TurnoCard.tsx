// Bloque de turno (color por estado).
import type { ReactElement } from "react";
import { estadoClasses } from "./estadoColor";
import { formatHora } from "./dateUtils";
import type { TurnoOut } from "../../shared/api/agenda";
import type { EstadoTurno } from "../../shared/api/agenda";
import { EstadoTurnoMenu } from "./EstadoTurnoMenu";

interface TurnoCardProps {
  turno: TurnoOut;
  pacienteNombre: string;
  profesionalNombre: string;
  rol: string;
  onCambiarEstado: (id: string, estado: EstadoTurno) => void;
}

export function TurnoCard({
  turno,
  pacienteNombre,
  profesionalNombre,
  rol,
  onCambiarEstado,
}: TurnoCardProps): ReactElement {
  return (
    <div className={`rounded border p-2 text-xs ${estadoClasses(turno.estado as EstadoTurno)}`}>
      <div className="font-semibold">
        {formatHora(turno.inicio)} – {formatHora(turno.fin)}
      </div>
      <div className="mt-1 font-medium">{pacienteNombre}</div>
      <div className="text-[11px] opacity-80">{profesionalNombre}</div>
      <div className="text-[11px] opacity-80">{turno.prestacion}</div>
      <div className="mt-1 text-[10px] uppercase tracking-wide">{turno.estado}</div>
      <EstadoTurnoMenu
        turnoId={turno.id}
        rol={rol}
        estadoActual={turno.estado as EstadoTurno}
        onCambiarEstado={onCambiarEstado}
      />
    </div>
  );
}