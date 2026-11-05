// Columna por sillón con turnos ordenados.
import type { ReactElement } from "react";
import type { Sillon } from "./types";
import type { TurnoOut } from "../../shared/api/agenda";
import { TurnoCard } from "./TurnoCard";

interface AgendaColumnProps {
  sillon: Sillon;
  turnos: TurnoOut[];
  pacienteNombre: (id: string) => string;
  profesionalNombre: (id: string) => string;
  rol: string;
  onCambiarEstado: (id: string, estado: import("../../shared/api/agenda").EstadoTurno) => void;
  onReprogramar: (turno: TurnoOut) => void;
}

export function AgendaColumn({
  sillon,
  turnos,
  pacienteNombre,
  profesionalNombre,
  rol,
  onCambiarEstado,
  onReprogramar,
}: AgendaColumnProps): ReactElement {
  const ordenados = [...turnos].sort((a, b) =>
    a.inicio < b.inicio ? -1 : a.inicio > b.inicio ? 1 : 0,
  );
  return (
    <div className="flex min-h-[200px] flex-col rounded border border-border bg-background">
      <div className="border-b border-border px-3 py-2 text-sm font-semibold">{sillon.nombre}</div>
      <div className="flex flex-1 flex-col gap-2 p-2">
        {ordenados.length === 0 ? (
          <p className="text-xs text-foreground/50">Sin turnos</p>
        ) : (
          ordenados.map((t) => (
            <TurnoCard
              key={t.id}
              turno={t}
              pacienteNombre={pacienteNombre(t.paciente_id)}
              profesionalNombre={profesionalNombre(t.profesional_id)}
              rol={rol}
              onCambiarEstado={onCambiarEstado}
              onReprogramar={onReprogramar}
            />
          ))
        )}
      </div>
    </div>
  );
}