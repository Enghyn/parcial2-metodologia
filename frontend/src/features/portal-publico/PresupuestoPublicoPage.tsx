// Página pública de presupuesto (C-18, task 5.2): /p/presupuesto/:token
// Lee el token de `useParams`, consulta presupuesto y pago en paralelo y permite
// aprobar (con firma simple) o rechazar. Ante 404 muestra una vista genérica (R9).
import type { ReactElement } from "react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  aprobarPresupuestoPublico,
  getPagoPublico,
  getPresupuestoPublico,
  rechazarPresupuestoPublico,
} from "../../shared/api/public";
import type { PagoPublico, PresupuestoPublico } from "../../shared/api/public";
import { FirmaSimple } from "./FirmaSimple";
import { ResumenPresupuesto } from "./ResumenPresupuesto";
import {
  MENSAJE_NO_ENCONTRADO,
  esErrorConflicto,
  esErrorNoEncontrado,
  estadoPagoLegible,
  vistaPresupuesto,
} from "./presentacion";

export function PresupuestoPublicoPage(): ReactElement {
  const { token } = useParams<{ token: string }>();
  const [presupuesto, setPresupuesto] = useState<PresupuestoPublico | null>(null);
  const [pago, setPago] = useState<PagoPublico | null>(null);
  const [firma, setFirma] = useState<string>("");
  const [noEncontrado, setNoEncontrado] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [enviando, setEnviando] = useState<boolean>(false);

  useEffect(() => {
    if (token === undefined) {
      setNoEncontrado(true);
      setLoading(false);
      return;
    }
    let activo = true;
    // Fetch en paralelo; el pago es opcional (409/404 esperados si aún no está aprobado).
    Promise.all([getPresupuestoPublico(token), getPagoPublico(token).catch(() => null)])
      .then(([presupuestoData, pagoData]) => {
        if (!activo) return;
        setPresupuesto(presupuestoData);
        setPago(pagoData);
      })
      .catch((err: unknown) => {
        if (!activo) return;
        if (esErrorNoEncontrado(err)) {
          setNoEncontrado(true);
        } else {
          setError(err instanceof Error ? err.message : "No pudimos cargar tu presupuesto.");
        }
      })
      .finally(() => {
        if (activo) setLoading(false);
      });
    return () => {
      activo = false;
    };
  }, [token]);

  async function responder(accion: "aprobar" | "rechazar"): Promise<void> {
    if (token === undefined) return;
    setEnviando(true);
    setError(null);
    try {
      const actualizado =
        accion === "aprobar"
          ? await aprobarPresupuestoPublico(token, firma)
          : await rechazarPresupuestoPublico(token);
      setPresupuesto(actualizado);
    } catch (err) {
      if (esErrorConflicto(err)) {
        setError("No pudimos registrar tu respuesta: el presupuesto ya no admite cambios.");
      } else {
        setError(err instanceof Error ? err.message : "No pudimos registrar tu respuesta.");
      }
    } finally {
      setEnviando(false);
    }
  }

  if (noEncontrado) {
    return (
      <section className="mx-auto max-w-xl space-y-4 p-6">
        <h1 className="text-2xl font-semibold">Presupuesto no disponible</h1>
        <p
          role="alert"
          className="rounded border border-rose-300 bg-rose-50 p-3 text-sm text-rose-700"
        >
          {MENSAJE_NO_ENCONTRADO}
        </p>
      </section>
    );
  }

  const vista = presupuesto !== null ? vistaPresupuesto(presupuesto) : null;

  return (
    <section className="mx-auto max-w-xl space-y-4 p-6">
      <h1 className="text-2xl font-semibold">Tu presupuesto</h1>

      {loading && <p className="text-sm text-foreground/60">Cargando tu presupuesto...</p>}
      {error !== null && (
        <p
          role="alert"
          className="rounded border border-rose-300 bg-rose-50 p-3 text-sm text-rose-700"
        >
          {error}
        </p>
      )}

      {presupuesto !== null && vista !== null && (
        <>
          <ResumenPresupuesto presupuesto={presupuesto} />

          {vista.puedeAprobar ? (
            <div className="space-y-2">
              <FirmaSimple
                firma={firma}
                onCambiarFirma={setFirma}
                onAprobar={() => void responder("aprobar")}
                enviando={enviando}
              />
              <button
                type="button"
                onClick={() => void responder("rechazar")}
                disabled={enviando}
                className="rounded border border-rose-300 px-4 py-2 text-sm text-rose-700 disabled:opacity-60"
              >
                {enviando ? "Procesando..." : "Rechazar presupuesto"}
              </button>
            </div>
          ) : (
            <p className="text-sm text-foreground/70">Ya registramos tu respuesta.</p>
          )}

          {pago !== null && (
            <p className="text-sm text-foreground/80">Pago: {estadoPagoLegible(pago.estado)}</p>
          )}

          {presupuesto.estado === "aprobado" && token !== undefined && (
            <Link to={`/p/pagar/${token}`} className="inline-block underline">
              Ir a pagar
            </Link>
          )}
        </>
      )}
    </section>
  );
}
