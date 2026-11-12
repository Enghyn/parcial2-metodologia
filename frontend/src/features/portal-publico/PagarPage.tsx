// Página de pago simulado (C-18, task 5.3): /p/pagar/:token
// Consulta el pago pendiente, muestra el monto en ARS y el resultado. El botón
// se deshabilita mientras la request está en curso (evita el doble submit).
import type { ReactElement } from "react";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { confirmarPagoPublico, getPagoPublico } from "../../shared/api/public";
import type { PagoPublico } from "../../shared/api/public";
import { ResultadoPago } from "./ResultadoPago";
import {
  MENSAJE_NO_DISPONIBLE,
  MENSAJE_NO_ENCONTRADO,
  esErrorConflicto,
  esErrorNoEncontrado,
  montoEnArs,
  puedeConfirmarPago,
} from "./presentacion";

export function PagarPage(): ReactElement {
  const { token } = useParams<{ token: string }>();
  const [pago, setPago] = useState<PagoPublico | null>(null);
  const [noEncontrado, setNoEncontrado] = useState<boolean>(false);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [confirmando, setConfirmando] = useState<boolean>(false);

  useEffect(() => {
    if (token === undefined) {
      setNoEncontrado(true);
      setLoading(false);
      return;
    }
    let activo = true;
    getPagoPublico(token)
      .then((data) => {
        if (activo) setPago(data);
      })
      .catch((err: unknown) => {
        if (!activo) return;
        if (esErrorNoEncontrado(err)) {
          setNoEncontrado(true);
        } else if (esErrorConflicto(err)) {
          setMensaje(MENSAJE_NO_DISPONIBLE);
        } else {
          setMensaje(err instanceof Error ? err.message : "No pudimos cargar el pago.");
        }
      })
      .finally(() => {
        if (activo) setLoading(false);
      });
    return () => {
      activo = false;
    };
  }, [token]);

  async function confirmar(): Promise<void> {
    if (token === undefined || pago === null || !puedeConfirmarPago(pago, confirmando)) {
      return;
    }
    setConfirmando(true);
    setMensaje(null);
    try {
      setPago(await confirmarPagoPublico(token));
    } catch (err) {
      setMensaje(err instanceof Error ? err.message : "No pudimos confirmar el pago.");
    } finally {
      setConfirmando(false);
    }
  }

  if (noEncontrado) {
    return (
      <section className="mx-auto max-w-xl space-y-4 p-6">
        <h1 className="text-2xl font-semibold">Pago no disponible</h1>
        <p
          role="alert"
          className="rounded border border-rose-300 bg-rose-50 p-3 text-sm text-rose-700"
        >
          {MENSAJE_NO_ENCONTRADO}
        </p>
      </section>
    );
  }

  return (
    <section className="mx-auto max-w-xl space-y-4 p-6">
      <h1 className="text-2xl font-semibold">Pagá tu seña</h1>

      {loading && <p className="text-sm text-foreground/60">Cargando el pago...</p>}
      {mensaje !== null && (
        <p
          role="alert"
          className="rounded border border-rose-300 bg-rose-50 p-3 text-sm text-rose-700"
        >
          {mensaje}
        </p>
      )}

      {pago !== null && (
        <div className="space-y-3 rounded border border-border p-4">
          <p className="text-lg font-medium">Monto a pagar: {montoEnArs(pago.monto)}</p>
          <ResultadoPago pago={pago} />
          <button
            type="button"
            onClick={() => void confirmar()}
            disabled={!puedeConfirmarPago(pago, confirmando)}
            className="rounded bg-primary px-4 py-2 text-primary-foreground disabled:opacity-60"
          >
            {confirmando ? "Confirmando..." : "Confirmar pago"}
          </button>
        </div>
      )}
    </section>
  );
}
