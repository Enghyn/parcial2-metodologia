// Navegación de semana: anterior, hoy y siguiente (D5).
import type { ReactElement } from "react";

interface SelectorSemanaProps {
  onAnterior: () => void;
  onHoy: () => void;
  onSiguiente: () => void;
  enSemanaActual: boolean;
}

const BOTON =
  "inline-flex min-h-11 flex-1 items-center justify-center gap-1 whitespace-nowrap rounded border border-border px-2 text-xs hover:bg-foreground/5 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary sm:flex-none sm:px-3 sm:text-sm";

export function SelectorSemana({
  onAnterior,
  onHoy,
  onSiguiente,
  enSemanaActual,
}: SelectorSemanaProps): ReactElement {
  return (
    <div
      className="flex w-full flex-wrap items-center gap-2 sm:w-auto"
      role="group"
      aria-label="Navegación de semana"
    >
      <button type="button" className={BOTON} onClick={onAnterior}>
        <span aria-hidden="true">←</span> Semana anterior
      </button>
      <button
        type="button"
        className={BOTON}
        onClick={onHoy}
        aria-current={enSemanaActual ? "date" : undefined}
      >
        Hoy
      </button>
      <button type="button" className={BOTON} onClick={onSiguiente}>
        Semana siguiente <span aria-hidden="true">→</span>
      </button>
    </div>
  );
}
