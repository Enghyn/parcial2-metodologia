// Resultado del pago simulado (C-18, task 5.3): aprobado/rechazado/pendiente.
import type { ReactElement } from "react";
import type { PagoPublico } from "../../shared/api/public";
import { resultadoPago } from "./presentacion";

interface ResultadoPagoProps {
  pago: PagoPublico;
}

export function ResultadoPago({ pago }: ResultadoPagoProps): ReactElement {
  const resultado = resultadoPago(pago);
  const estilo = resultado.aprobado
    ? "border-emerald-300 bg-emerald-50 text-emerald-700"
    : resultado.rechazado
      ? "border-rose-300 bg-rose-50 text-rose-700"
      : "border-border bg-background text-foreground/80";

  return (
    <p role="status" className={`rounded border p-3 text-sm ${estilo}`}>
      {resultado.texto}
    </p>
  );
}
