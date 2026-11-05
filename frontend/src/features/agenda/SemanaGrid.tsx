// Grilla semanal 7 días × N sillones activos (D6). Sin handler en celdas vacías.
import type { ReactElement } from "react";
import { useMemo } from "react";
import type { EstadoTurno, TurnoOut } from "../../shared/api/agenda";
import { TurnoChip } from "./TurnoChip";
import type { Sillon } from "./types";
import { agruparSemana, claveCelda, diasSemana, formatearRangoSemana } from "./semanaUtils";

interface SemanaGridProps {
  lunes: string;
  sillones: Sillon[];
  turnos: TurnoOut[];
  hoyIso: string;
  rol: string;
  seleccionadoId: string | null;
  pacienteNombre: (id: string) => string;
  profesionalNombre: (id: string) => string;
  onSeleccionar: (turno: TurnoOut) => void;
  onCambiarEstado: (id: string, estado: EstadoTurno) => void;
  onReprogramar: (turno: TurnoOut) => void;
}

export function SemanaGrid({
  lunes,
  sillones,
  turnos,
  hoyIso,
  rol,
  seleccionadoId,
  pacienteNombre,
  profesionalNombre,
  onSeleccionar,
  onCambiarEstado,
  onReprogramar,
}: SemanaGridProps): ReactElement {
  const dias = useMemo(() => diasSemana(lunes), [lunes]);
  const activos = useMemo(() => sillones.filter((sillon) => sillon.activo), [sillones]);
  const grupos = useMemo(() => agruparSemana(turnos, lunes), [turnos, lunes]);

  return (
    <div>
      <p className="mb-2 text-[11px] text-foreground/60 md:hidden" aria-hidden="true">
        Deslizá la grilla para ver los 7 días →
      </p>
      <div
        className="overflow-x-auto rounded border border-border"
        role="region"
        aria-label="Grilla semanal"
        tabIndex={0}
      >
        <table className="w-full min-w-[940px] table-fixed border-collapse text-xs">
          <caption className="sr-only">
            Turnos de la semana del {formatearRangoSemana(lunes)}, por sillón y día
          </caption>
          <colgroup>
            <col className="w-[82px]" />
            {dias.map((dia) => (
              <col key={dia.iso} />
            ))}
          </colgroup>
          <thead>
            <tr>
              <td className="w-[82px] border-b border-border bg-foreground/[0.03] p-1.5">
                <span className="sr-only">Sillón</span>
              </td>
              {dias.map((dia) => {
                const esHoy = dia.iso === hoyIso;
                return (
                  <th
                    key={dia.iso}
                    scope="col"
                    className={`border-b border-border bg-foreground/[0.03] p-1.5 text-left align-middle ${
                      esHoy ? "bg-primary/10 shadow-[inset_0_-2px_0_var(--color-primary)]" : ""
                    }`}
                  >
                    <span className="flex items-baseline gap-1.5">
                      <span className="text-xs font-semibold">{dia.nombre}</span>
                      <span className="text-[10px] tabular-nums text-foreground/60">
                        {dia.dia} {dia.mes}
                      </span>
                    </span>
                    {esHoy && (
                      <span className="mt-0.5 inline-flex rounded-full border border-primary px-1.5 text-[10px] font-semibold uppercase text-primary">
                        Hoy
                      </span>
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {activos.map((sillon) => (
              <tr key={sillon.id}>
                <th
                  scope="row"
                  className="sticky left-0 z-10 w-[82px] border-b border-border bg-foreground/[0.03] p-1.5 text-left align-middle text-xs font-semibold"
                >
                  {sillon.nombre}
                </th>
                {dias.map((dia) => {
                  const turnosCelda = grupos[claveCelda(sillon.id, dia.iso)] ?? [];
                  const esHoy = dia.iso === hoyIso;
                  return (
                    <td
                      key={dia.iso}
                      className={`break-words border-b border-l border-border p-1 align-top ${
                        esHoy ? "bg-primary/5" : ""
                      }`}
                    >
                      {turnosCelda.length === 0 ? (
                        <span className="block min-h-10 text-[10px] leading-10 text-foreground/50">
                          Libre
                        </span>
                      ) : (
                        <div className="grid gap-1">
                          {turnosCelda.map((turno) => (
                            <TurnoChip
                              key={turno.id}
                              turno={turno}
                              dia={dia}
                              pacienteNombre={pacienteNombre(turno.paciente_id)}
                              profesionalNombre={profesionalNombre(turno.profesional_id)}
                              rol={rol}
                              seleccionado={seleccionadoId === turno.id}
                              onSeleccionar={onSeleccionar}
                              onCambiarEstado={onCambiarEstado}
                              onReprogramar={onReprogramar}
                            />
                          ))}
                        </div>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
