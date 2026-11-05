// Vista pública de un turno por token (C-06, D6/D9): datos, WhatsApp y cancelación.
import type { ReactElement } from "react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  cancelarTurnoPublico,
  getTurnoPublico,
} from "../../shared/api/public";
import type { TurnoPublicoOut } from "../../shared/api/public";
import { QrTurno } from "./QrTurno";
import { WhatsappButton } from "./WhatsappButton";
import { formatFecha, formatHora } from "./types";

export function TurnoPublicoPage(): ReactElement {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const [turno, setTurno] = useState<TurnoPublicoOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [cancelando, setCancelando] = useState<boolean>(false);

  useEffect(() => {
    if (token === undefined) {
      setError("Falta el token del turno.");
      setLoading(false);
      return;
    }
    let activo = true;
    getTurnoPublico(token)
      .then((data) => {
        if (activo) setTurno(data);
      })
      .catch(() => {
        if (activo) setError("No encontramos tu turno.");
      })
      .finally(() => {
        if (activo) setLoading(false);
      });
    return () => {
      activo = false;
    };
  }, [token]);

  async function handleCancelar(): Promise<void> {
    if (token === undefined) return;
    setCancelando(true);
    setError(null);
    try {
      setTurno(await cancelarTurnoPublico(token));
    } catch (err) {
      setError(err instanceof Error ? err.message : "No pudimos cancelar el turno.");
    } finally {
      setCancelando(false);
    }
  }

  return (
    <section className="mx-auto max-w-xl space-y-4 p-6">
      <h1 className="text-2xl font-semibold">Tu turno</h1>

      {loading && <p className="text-sm text-foreground/60">Cargando tu turno...</p>}
      {error !== null && (
        <p role="alert" className="rounded border border-rose-300 bg-rose-50 p-3 text-sm text-rose-700">
          {error}
        </p>
      )}

      {turno !== null && (
        <div className="space-y-3 rounded border border-border p-4">
          <p className="text-lg font-medium">{turno.prestacion}</p>
          <p className="text-sm">
            {formatFecha(turno.inicio)} a las {formatHora(turno.inicio)} hs
          </p>
          <ul className="space-y-1 text-sm text-foreground/80">
            <li>Paciente: {turno.paciente_nombre}</li>
            <li>Profesional: {turno.profesional_nombre}</li>
            <li>Sillón: {turno.sillon_nombre}</li>
            <li>Duración: {turno.duracion_min} minutos</li>
            <li className="font-medium uppercase tracking-wide">Estado: {turno.estado}</li>
          </ul>

          <QrTurno token={turno.token} />

          {turno.estado !== "cancelado" ? (
            <div className="flex flex-wrap items-center gap-2 pt-2">
              <WhatsappButton turno={turno} />
              {(turno.estado === "reservado" || turno.estado === "confirmado") && token !== undefined && (
                <button
                  type="button"
                  onClick={() => navigate(`/p/turno/${token}/reprogramar`)}
                  className="rounded border border-border px-4 py-2 text-sm"
                >
                  Reprogramar
                </button>
              )}
              <button
                type="button"
                onClick={() => void handleCancelar()}
                disabled={cancelando}
                className="rounded border border-rose-300 px-4 py-2 text-rose-700 disabled:opacity-60"
              >
                {cancelando ? "Cancelando..." : "Cancelar turno"}
              </button>
            </div>
          ) : (
            <p className="pt-2 text-sm font-medium text-rose-700">Este turno está cancelado.</p>
          )}
        </div>
      )}
    </section>
  );
}
