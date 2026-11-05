import type { ReactElement } from "react";
import { useState } from "react";
import { rutaQrReserva } from "../../shared/api/public";

export function QrPortal(): ReactElement {
  const [abierto, setAbierto] = useState<boolean>(false);
  return (
    <div className="rounded border border-border p-3">
      <button
        type="button"
        onClick={() => setAbierto((v) => !v)}
        className="text-sm font-medium underline"
        aria-expanded={abierto}
      >
        Compartí el portal
      </button>
      {abierto && (
        <div className="mt-3 space-y-2">
          <img
            src={rutaQrReserva()}
            alt="Código QR para reservar un turno"
            className="h-32 w-32"
          />
          <p className="text-xs text-foreground/70">
            Escaneá este código para abrir el portal de reservas.
          </p>
        </div>
      )}
    </div>
  );
}