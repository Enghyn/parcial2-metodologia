// Paso 3 del wizard: día y horario libre (consume /public/disponibilidad).
import type { ReactElement } from "react";
import { useEffect, useState } from "react";
import {
  getDisponibilidad,
  listarProfesionalesPublicos,
} from "../../../shared/api/public";
import type { SlotPublico } from "../../../shared/api/public";
import { formatHora, toIsoDate } from "../types";

interface PasoHorarioProps {
  duracionMin: number;
  profesionalId: string | null;
  onSelect: (slot: SlotPublico) => void;
  onBack: () => void;
}

export function PasoHorario({
  duracionMin,
  profesionalId,
  onSelect,
  onBack,
}: PasoHorarioProps): ReactElement {
  const [fecha, setFecha] = useState<string>(toIsoDate(new Date()));
  const [slots, setSlots] = useState<SlotPublico[]>([]);
  const [nombres, setNombres] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let activo = true;
    listarProfesionalesPublicos()
      .then((data) => {
        if (!activo) return;
        const mapa: Record<string, string> = {};
        data.forEach((p) => {
          mapa[p.id] = p.nombre;
        });
        setNombres(mapa);
      })
      .catch(() => {
        if (activo) setNombres({});
      });
    return () => {
      activo = false;
    };
  }, []);

  useEffect(() => {
    let activo = true;
    setLoading(true);
    setError(null);
    getDisponibilidad({
      fecha,
      duracion_min: duracionMin,
      profesional_id: profesionalId ?? undefined,
    })
      .then((data) => {
        if (activo) setSlots(data);
      })
      .catch(() => {
        if (!activo) return;
        setSlots([]);
        setError("No pudimos cargar la disponibilidad. Probá de nuevo.");
      })
      .finally(() => {
        if (activo) setLoading(false);
      });
    return () => {
      activo = false;
    };
  }, [fecha, duracionMin, profesionalId]);

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">3. Elegí día y horario</h2>
      <label className="block text-sm font-medium">
        Fecha
        <input
          type="date"
          value={fecha}
          onChange={(event) => setFecha(event.target.value)}
          className="mt-1 w-full rounded border border-border px-3 py-2"
        />
      </label>
      {error !== null && <p className="text-sm text-rose-600">{error}</p>}
      {loading && <p className="text-sm text-foreground/60">Buscando horarios libres...</p>}
      {!loading && slots.length === 0 && error === null && (
        <p className="text-sm text-foreground/60">
          No hay horarios libres para ese día. Probá con otra fecha.
        </p>
      )}
      <ul className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {slots.map((slot) => (
          <li key={`${slot.inicio}-${slot.profesional_id}`}>
            <button
              type="button"
              onClick={() => onSelect(slot)}
              className="w-full rounded border border-border p-2 text-left hover:border-primary"
            >
              <span className="block font-semibold">{formatHora(slot.inicio)}</span>
              <span className="text-xs text-foreground/60">
                {nombres[slot.profesional_id] ?? "Profesional"}
              </span>
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
