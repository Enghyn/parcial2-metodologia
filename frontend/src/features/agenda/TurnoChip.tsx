// Chip compacto de turno en la grilla semanal (D6/D10): compone el menú de
// estado y la acción de reprogramar de C-09a sin duplicar su lógica.
import type { ReactElement } from "react";
import type { EstadoTurno, TurnoOut } from "../../shared/api/agenda";
import { estadoClasses } from "./estadoColor";
import { formatHora } from "./dateUtils";
import { EstadoTurnoMenu } from "./EstadoTurnoMenu";
import type { DiaSemana } from "./semanaUtils";

interface TurnoChipProps {
  turno: TurnoOut;
  dia: DiaSemana;
  pacienteNombre: string;
  profesionalNombre: string;
  rol: string;
  seleccionado: boolean;
  onSeleccionar: (turno: TurnoOut) => void;
  onCambiarEstado: (id: string, estado: EstadoTurno) => void;
  onReprogramar: (turno: TurnoOut) => void;
}

export function TurnoChip({
  turno,
  dia,
  pacienteNombre,
  profesionalNombre,
  rol,
  seleccionado,
  onSeleccionar,
  onCambiarEstado,
  onReprogramar,
}: TurnoChipProps): ReactElement {
  const hora = `${formatHora(turno.inicio)}–${formatHora(turno.fin)}`;
  const etiqueta = [
    `${dia.nombre} ${dia.dia}`,
    `${formatHora(turno.inicio)} a ${formatHora(turno.fin)}`,
    turno.prestacion,
    pacienteNombre,
    profesionalNombre,
    turno.estado,
    turno.es_sobreturno ? "sobreturno" : null,
  ]
    .filter((parte): parte is string => parte !== null)
    .join(", ");
  const puedeReprogramar = rol === "admin" || rol === "recepcion";

  return (
    <div
      className={`break-words rounded border ${estadoClasses(turno.estado)} ${
        turno.es_sobreturno ? "border-dashed" : ""
      } ${seleccionado ? "ring-2 ring-primary ring-offset-1" : ""}`}
      data-estado={turno.estado}
    >
      <button
        type="button"
        aria-label={etiqueta}
        aria-expanded={seleccionado}
        onClick={() => onSeleccionar(turno)}
        className="block min-h-11 w-full p-1 text-left focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
      >
        {turno.es_sobreturno && (
          <span className="mb-0.5 inline-block rounded border border-dashed border-current px-1 text-[10px] font-bold uppercase tracking-wide">
            Sobreturno
          </span>
        )}
        <span className="block text-[10px] font-bold tabular-nums">{hora}</span>
        <span className="block text-xs font-semibold leading-tight">{pacienteNombre}</span>
        <span className="block text-[10px] opacity-90">
          {turno.prestacion} · {profesionalNombre}
        </span>
        <span className="mt-0.5 flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wide">
          <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-current" />
          {turno.estado}
        </span>
      </button>

      {seleccionado && (
        <div className="border-t border-current/20 p-1">
          <EstadoTurnoMenu
            turnoId={turno.id}
            rol={rol}
            estadoActual={turno.estado}
            onCambiarEstado={onCambiarEstado}
          />
          {puedeReprogramar && (
            <button
              type="button"
              onClick={() => onReprogramar(turno)}
              className="mt-1 min-h-11 w-full rounded border border-border bg-background px-2 text-[11px] hover:bg-foreground/5 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            >
              Reprogramar
            </button>
          )}
        </div>
      )}
    </div>
  );
}
