// Selector de fecha (hoy/anterior/siguiente).
import type { ReactElement } from "react";
import { addDays, toIsoDate } from "./dateUtils";

interface DateSelectorProps {
  fecha: string;
  onChange: (fecha: string) => void;
}

export function DateSelector({ fecha, onChange }: DateSelectorProps): ReactElement {
  const current = new Date(`${fecha}T00:00:00`);
  function ir(delta: number): void {
    onChange(toIsoDate(addDays(current, delta)));
  }
  function irHoy(): void {
    onChange(toIsoDate(new Date()));
  }
  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        type="button"
        onClick={() => ir(-1)}
        className="inline-flex min-h-11 items-center rounded border border-border px-3"
      >
        Anterior
      </button>
      <button
        type="button"
        onClick={irHoy}
        className="inline-flex min-h-11 items-center rounded border border-border px-3"
      >
        Hoy
      </button>
      <button
        type="button"
        onClick={() => ir(1)}
        className="inline-flex min-h-11 items-center rounded border border-border px-3"
      >
        Siguiente
      </button>
      <span className="text-sm font-medium sm:ml-2">{fecha}</span>
    </div>
  );
}