// Filtro por profesional aplicado en cliente (D7): no dispara otra request.
import type { ReactElement } from "react";
import type { Profesional } from "./types";

interface FiltroProfesionalProps {
  profesionales: Profesional[];
  valor: string | null;
  onChange: (profesionalId: string | null) => void;
}

const VALOR_TODOS = "";

export function FiltroProfesional({
  profesionales,
  valor,
  onChange,
}: FiltroProfesionalProps): ReactElement {
  return (
    <div className="flex min-h-11 w-full items-center gap-2 sm:w-auto">
      <label htmlFor="filtro-profesional" className="text-[11px] font-semibold uppercase tracking-wide text-foreground/60">
        Profesional
      </label>
      <select
        id="filtro-profesional"
        className="min-h-11 rounded border border-border bg-background px-2 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
        value={valor ?? VALOR_TODOS}
        onChange={(event) => {
          const seleccionado = event.target.value;
          onChange(seleccionado === VALOR_TODOS ? null : seleccionado);
        }}
      >
        <option value={VALOR_TODOS}>Todos los profesionales</option>
        {profesionales.map((profesional) => (
          <option key={profesional.id} value={profesional.id}>
            {profesional.nombre}
          </option>
        ))}
      </select>
    </div>
  );
}
