// Historial de cambios por pieza (C-11): línea de tiempo append-only.
// Los tres roles pueden leerlo.
import type { ReactElement } from "react";
import { useEffect, useState } from "react";
import { getHistorialPieza } from "../../shared/api/clinica";
import type { HistorialPieza } from "../../shared/api/clinica";

interface HistorialPiezaProps {
  pacienteId: string;
  pieza: number;
}

export function HistorialPieza({ pacienteId, pieza }: HistorialPiezaProps): ReactElement {
  const [historial, setHistorial] = useState<HistorialPieza[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    getHistorialPieza(pacienteId, pieza)
      .then((h) => setHistorial(h))
      .catch(() => setError("No pudimos cargar el historial de la pieza."))
      .finally(() => setLoading(false));
  }, [pacienteId, pieza]);

  return (
    <section className="space-y-4 p-4">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold">Historial por pieza</h2>
        <p className="text-sm text-foreground/70">
          Cada cambio de estado queda registrado con autor y fecha. No se pisa el hallazgo anterior.
        </p>
      </header>

      {loading && <p className="text-sm text-foreground/60">Cargando historial...</p>}
      {error !== null && <p className="text-sm text-rose-600">{error}</p>}

      {historial.length === 0 && !loading && (
        <div className="rounded border border-border p-3 text-center">
          <span className="text-xl text-foreground/40">🦷</span>
          <p className="mt-2 text-sm text-foreground/60">
            Sin historial para esta pieza
          </p>
          <p className="text-xs text-foreground/50">
            Los cambios de estado se registran automáticamente.
          </p>
        </div>
      )}

      <div className="space-y-2 pl-4">
        {historial.map((h, idx) => (
          <div key={`historial-${idx}`} className="flex gap-3">
            <span className="w-2 h-2 rounded-full bg-primary"></span>
            <div className="flex-1 border-l border-border pl-3 py-1">
              <div className="flex items-center gap-2 text-sm">
                <span className="font-semibold text-foreground">{h.estado_anterior ?? "—"}</span>
                <span className="text-xs font-medium text-foreground/50">→</span>
                <span className="font-semibold text-primary">{h.estado_nuevo}</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-foreground/50 mt-1">
                <span>{h.observacion_anterior ?? "—"}</span>
                <span>→</span>
                <span>{h.observacion_nueva ?? "—"}</span>
              </div>
              <div className="text-xs text-foreground/50">
                {new Date(h.registrado_en).toLocaleString("es-AR")}
                {" · "}
                {h.registrado_por?.slice(0, 8) ?? "—"}
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
