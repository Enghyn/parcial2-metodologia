// Paso 1 del wizard: elección de prestación (catálogo estático).
import type { ReactElement } from "react";
import { PRESTACIONES, type Prestacion } from "../types";

interface PasoPrestacionProps {
  onSelect: (prestacion: Prestacion) => void;
}

export function PasoPrestacion({ onSelect }: PasoPrestacionProps): ReactElement {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">1. Elegí la prestación</h2>
      <ul className="grid gap-2 sm:grid-cols-2">
        {PRESTACIONES.map((prestacion) => (
          <li key={prestacion.nombre}>
            <button
              type="button"
              onClick={() => onSelect(prestacion)}
              className="w-full rounded border border-border p-3 text-left hover:border-primary"
            >
              <span className="block font-medium">{prestacion.nombre}</span>
              <span className="text-sm text-foreground/60">
                {prestacion.duracion_min} minutos
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
