// Paso 2 del wizard: elección de profesional (o "cualquiera disponible").
import type { ReactElement } from "react";
import { useEffect, useState } from "react";
import { listarProfesionalesPublicos } from "../../../shared/api/public";
import type { ProfesionalPublico } from "../../../shared/api/public";

interface PasoProfesionalProps {
  onSelect: (profesionalId: string | null) => void;
  onBack: () => void;
}

export function PasoProfesional({ onSelect, onBack }: PasoProfesionalProps): ReactElement {
  const [profesionales, setProfesionales] = useState<ProfesionalPublico[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let activo = true;
    listarProfesionalesPublicos()
      .then((data) => {
        if (activo) setProfesionales(data);
      })
      .catch(() => {
        if (activo) setError("No pudimos cargar los profesionales.");
      });
    return () => {
      activo = false;
    };
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">2. Elegí el profesional</h2>
      {error !== null && <p className="text-sm text-rose-600">{error}</p>}
      <ul className="grid gap-2 sm:grid-cols-2">
        <li>
          <button
            type="button"
            onClick={() => onSelect(null)}
            className="w-full rounded border border-border p-3 text-left hover:border-primary"
          >
            <span className="block font-medium">Cualquiera disponible</span>
            <span className="text-sm text-foreground/60">
              Te asignamos el primer horario libre
            </span>
          </button>
        </li>
        {profesionales.map((profesional) => (
          <li key={profesional.id}>
            <button
              type="button"
              onClick={() => onSelect(profesional.id)}
              className="w-full rounded border border-border p-3 text-left hover:border-primary"
            >
              <span className="block font-medium">{profesional.nombre}</span>
            </button>
          </li>
        ))}
      </ul>
      <button type="button" onClick={onBack} className="text-sm underline">
        Volver
      </button>
    </div>
  );
}
