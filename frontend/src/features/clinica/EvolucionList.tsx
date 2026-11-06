// Lista de evolución clínica (C-11): notas append-only con autor y fecha.
// Solo el odontólogo puede agregar notas; los tres roles pueden leer.
import type { ReactElement } from "react";
import { useEffect, useState } from "react";
import { useAuthStore } from "../../app/AuthContext";
import {
  crearEvolucion,
  Evolucion,
  listarEvoluciones,
} from "../../shared/api/clinica";

interface EvolucionListProps {
  pacienteId: string;
}

export function EvolucionList({ pacienteId }: EvolucionListProps): ReactElement {
  const user = useAuthStore((s) => s.user);
  const canEdit = user?.rol === "odontologo";
  const [evoluciones, setEvoluciones] = useState<Evolucion[]>([]);
  const [texto, setTexto] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);

  useEffect(() => {
    setLoading(true);
    listarEvoluciones(pacienteId)
      .then((evo) => setEvoluciones(evo))
      .catch(() => setError("No pudimos cargar las notas de evolución."))
      .finally(() => setLoading(false));
  }, [pacienteId]);

  async function guardar(): Promise<void> {
    if (texto.trim() === "" || !canEdit) return;
    setGuardando(true);
    setError(null);
    try {
      await crearEvolucion(pacienteId, { texto: texto.trim() });
      setTexto("");
      const actualizadas = await listarEvoluciones(pacienteId);
      setEvoluciones(actualizadas);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No pudimos guardar la nota.");
    } finally {
      setGuardando(false);
    }
  }

  return (
    <section className="space-y-4 p-4">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold">Evolución clínica</h2>
        <p className="text-sm text-foreground/70">
          Append-only: cada nota queda con fecha y autor. No se pisa ni se borra.
        </p>
      </header>

      {loading && <p className="text-sm text-foreground/60">Cargando evolución...</p>}
      {error !== null && <p className="text-sm text-rose-600">{error}</p>}

      {evoluciones.length === 0 && !loading && (
        <div className="rounded border border-border p-3 text-center">
          <p className="text-sm text-foreground/60">Sin notas de evolución.</p>
        </div>
      )}

      {evoluciones.map((e) => (
        <div key={e.id} className="rounded border border-border p-3">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
            <span className="text-sm font-medium text-foreground">{e.texto}</span>
            <span className="text-xs text-foreground/50">
              {new Date(e.fecha).toLocaleString("es-AR")}
            </span>
            <span className="text-xs text-foreground/50">
              {e.autor_usuario_id.slice(0, 8)}
            </span>
          </div>
        </div>
      ))}

      {canEdit && (
        <div className="rounded border border-border p-3">
          <h2 className="text-sm font-semibold mb-2">Nueva nota de evolución</h2>
          <label className="block text-sm mb-1">
            Nota clínica
            <textarea
              value={texto}
              onChange={(event) => setTexto(event.target.value)}
              rows={3}
              className="mt-1 w-full rounded border border-border px-3 py-2"
              placeholder="Describí la evolución del paciente..."
            />
          </label>
          <div className="mt-2 flex justify-end gap-2">
            <button
              type="button"
              onClick={() => void guardar()}
              disabled={guardando || texto.trim() === ""}
              className="rounded bg-primary px-4 py-2 text-primary-foreground disabled:opacity-60 text-sm font-medium"
            >
              {guardando ? "Guardando..." : "Guardar nota"}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
