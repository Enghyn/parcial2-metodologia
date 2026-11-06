// Lista de consentimiento informado (C-11): versiones registradas con autor y fecha.
// Solo el odontólogo puede agregar versiones; los tres roles pueden leer.
import type { ReactElement } from "react";
import { useEffect, useState } from "react";
import { useAuthStore } from "../../app/AuthContext";
import {
  crearConsentimiento,
  Consentimiento,
  listarConsentimientos,
} from "../../shared/api/clinica";

interface ConsentimientoListProps {
  pacienteId: string;
}

export function ConsentimientoList({ pacienteId }: ConsentimientoListProps): ReactElement {
  const user = useAuthStore((s) => s.user);
  const canEdit = user?.rol === "odontologo";
  const [consentimientos, setConsentimientos] = useState<Consentimiento[]>([]);
  const [version, setVersion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);

  useEffect(() => {
    setLoading(true);
    listarConsentimientos(pacienteId)
      .then((cs) => setConsentimientos(cs))
      .catch(() => setError("No pudimos cargar los consentimientos."))
      .finally(() => setLoading(false));
  }, [pacienteId]);

  async function guardar(): Promise<void> {
    if (version.trim() === "" || !canEdit) return;
    setGuardando(true);
    setError(null);
    try {
      await crearConsentimiento(pacienteId, { version: version.trim() });
      const actualizadas = await listarConsentimientos(pacienteId);
      setConsentimientos(actualizadas);
      setVersion("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "No pudimos registrar el consentimiento.");
    } finally {
      setGuardando(false);
    }
  }

  return (
    <section className="space-y-4 p-4">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold">Consentimiento informado</h2>
        <p className="text-sm text-foreground/70">
          Cada versión queda registrada con fecha y autor. Una versión nueva no pisa la anterior.
        </p>
      </header>

      {loading && <p className="text-sm text-foreground/60">Cargando consentimientos...</p>}
      {error !== null && <p className="text-sm text-rose-600">{error}</p>}

      {consentimientos.length === 0 && !loading && (
        <div className="rounded border border-border p-3 text-center">
          <p className="text-sm text-foreground/60">Sin consentimientos registrados.</p>
        </div>
      )}

      {consentimientos.map((c) => (
        <div key={c.id} className="rounded border border-border p-3">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
            <span className="text-sm font-semibold text-foreground">v{c.version}</span>
            <span className="text-xs text-foreground/50">
              {new Date(c.fecha).toLocaleString("es-AR")}
            </span>
            <span className="text-xs text-foreground/50">
              {c.autor_usuario_id.slice(0, 8)}
            </span>
          </div>
        </div>
      ))}

      {canEdit && (
        <div className="rounded border border-border p-3">
          <h2 className="text-sm font-semibold mb-2">Registrar nueva versión</h2>
          <label className="block text-sm mb-1">
            Versión
            <input
              value={version}
              onChange={(event) => setVersion(event.target.value)}
              className="mt-1 w-full rounded border border-border px-3 py-2"
              placeholder="Ej: v3"
            />
          </label>
          <div className="mt-2 flex justify-end gap-2">
            <button
              type="button"
              onClick={() => void guardar()}
              disabled={guardando || version.trim() === ""}
              className="rounded bg-primary px-4 py-2 text-primary-foreground disabled:opacity-60 text-sm font-medium"
            >
              {guardando ? "Registrando..." : "Registrar"}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
