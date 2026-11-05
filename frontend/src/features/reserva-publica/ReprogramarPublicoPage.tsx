import type { ReactElement } from "react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getDisponibilidad, reprogramarTurnoPublico } from "../../shared/api/public";
import type { SlotPublico } from "../../shared/api/public";
import { formatFecha, formatHora } from "./types";

export function ReprogramarPublicoPage(): ReactElement {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const [fecha, setFecha] = useState<string>("");
  const [slots, setSlots] = useState<SlotPublico[]>([]);
  const [selected, setSelected] = useState<SlotPublico | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState<boolean>(false);

  async function cargar(fechaElegida: string): Promise<void> {
    if (token === undefined) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getDisponibilidad({ fecha: fechaElegida, duracion_min: 30 });
      setSlots(data);
      setSelected(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No pudimos cargar los horarios.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (fecha !== "") void cargar(fecha);
  }, [fecha]);

  async function confirmar(): Promise<void> {
    if (token === undefined || selected === null) return;
    setEnviando(true);
    setError(null);
    try {
      await reprogramarTurnoPublico(token, { inicio: selected.inicio });
      navigate(`/p/turno/${token}`, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "No pudimos reprogramar el turno.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section className="mx-auto max-w-2xl space-y-4 p-6">
      <h1 className="text-2xl font-semibold">Reprogramar turno</h1>
      {error !== null && (
        <p role="alert" className="rounded border border-rose-300 bg-rose-50 p-3 text-sm text-rose-700">
          {error}
        </p>
      )}
      <label className="block text-sm font-medium">
        Día
        <input
          type="date"
          value={fecha}
          onChange={(e) => setFecha(e.target.value)}
          className="mt-1 w-full rounded border border-border px-3 py-2"
        />
      </label>
      {loading && <p className="text-sm text-foreground/60">Cargando horarios...</p>}
      {slots.length > 0 && (
        <ul className="space-y-2">
          {slots.map((s) => (
            <li key={`${s.inicio}-${s.sillon_id}`}>
              <button
                type="button"
                onClick={() => setSelected(s)}
                className={`w-full rounded border px-3 py-2 text-left text-sm ${selected === s ? "border-primary bg-primary/10" : "border-border"}`}
              >
                {formatFecha(s.inicio)} a las {formatHora(s.inicio)}
              </button>
            </li>
          ))}
        </ul>
      )}
      {selected !== null && (
        <div className="space-y-2">
          <p className="text-sm">
            Nuevo horario: {formatFecha(selected.inicio)} a las {formatHora(selected.inicio)}
          </p>
          <button
            type="button"
            onClick={() => void confirmar()}
            disabled={enviando}
            className="rounded bg-primary px-4 py-2 text-primary-foreground disabled:opacity-60"
          >
            {enviando ? "Reprogramando..." : "Confirmar reprogramación"}
          </button>
        </div>
      )}
    </section>
  );
}