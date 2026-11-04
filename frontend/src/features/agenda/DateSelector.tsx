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
    <div className="flex items-center gap-2">
      <button type="button" onClick={() => ir(-1)} className="rounded border border-border px-3 py-1">
        Anterior
      </button>
      <button type="button" onClick={irHoy} className="rounded border border-border px-3 py-1">
        Hoy
      </button>
      <button type="button" onClick={() => ir(1)} className="rounded border border-border px-3 py-1">
        Siguiente
      </button>
      <span className="ml-2 text-sm font-medium">{fecha}</span>
    </div>
  );
}