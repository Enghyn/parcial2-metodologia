import type { ReactElement } from "react";
import { rutaQrTurno } from "../../shared/api/public";

interface QrTurnoProps {
  token: string;
}

export function QrTurno({ token }: QrTurnoProps): ReactElement {
  return (
    <div className="space-y-1">
      <img
        src={rutaQrTurno(token)}
        alt="Código QR de tu turno"
        className="h-32 w-32"
      />
      <p className="text-xs text-foreground/70">Mostrá este código en recepción</p>
    </div>
  );
}