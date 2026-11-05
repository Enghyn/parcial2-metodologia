// Modal de reprogramación de turno (C-09a).
import type { FormEvent, ReactElement } from "react";
import { useEffect, useState } from "react";
import type { ReprogramarInput, TurnoOut } from "../../shared/api/agenda";
import { localInputToUtc, toLocalInput } from "./dateUtils";

interface ReprogramarModalProps {
  turno: TurnoOut | null;
  onClose: () => void;
  onReprogramar: (id: string, datos: ReprogramarInput) => Promise<void>;
}

export function ReprogramarModal({
  turno,
  onClose,
  onReprogramar,
}: ReprogramarModalProps): ReactElement | null {
  const [inicio, setInicio] = useState<string>("");
  const [duracion, setDuracion] = useState<string>("30");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<boolean>(false);

  useEffect(() => {
    if (turno !== null) {
      setInicio(toLocalInput(turno.inicio));
      setDuracion(String(turno.duracion_min));
      setError(null);
      setPending(false);
    }
  }, [turno]);

  if (turno === null) return null;

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    if (turno === null) return;
    if (inicio === "" || Number(duracion) <= 0) {
      setError("Completá el nuevo horario y una duración mayor a cero.");
      return;
    }
    setPending(true);
    try {
      await onReprogramar(turno.id, {
        inicio: localInputToUtc(inicio),
        duracion_min: Number(duracion),
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo reprogramar el turno.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded bg-background p-6 shadow-lg">
        <h2 className="text-lg font-semibold">Reprogramar turno</h2>
        <p className="mt-1 text-sm text-foreground/70">
          {turno.prestacion} · actual: {new Date(turno.inicio).toLocaleString("es-AR")}
        </p>
        <form onSubmit={(e) => void handleSubmit(e)} className="mt-4 space-y-3">
          <label className="block text-sm font-medium">
            Nuevo inicio
            <input
              type="datetime-local"
              value={inicio}
              onChange={(e) => setInicio(e.target.value)}
              className="mt-1 w-full rounded border border-border px-3 py-2"
            />
          </label>
          <label className="block text-sm font-medium">
            Duración (min)
            <input
              type="number"
              min={1}
              value={duracion}
              onChange={(e) => setDuracion(e.target.value)}
              className="mt-1 w-full rounded border border-border px-3 py-2"
            />
          </label>
          {error !== null && <p className="text-sm text-rose-600">{error}</p>}
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={pending}
              className="rounded border border-border px-4 py-2"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={pending}
              className="rounded bg-primary px-4 py-2 text-primary-foreground disabled:opacity-60"
            >
              {pending ? "Guardando..." : "Reprogramar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
