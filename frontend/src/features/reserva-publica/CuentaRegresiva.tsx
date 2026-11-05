import type { ReactElement } from "react";
import { useEffect, useState } from "react";
import { formatearCuentaRegresiva, retencionVencida, segundosRestantes } from "./retencion";

interface CuentaRegresivaProps {
  expiraEn: string;
  onVencida?: () => void;
}

export function CuentaRegresiva({ expiraEn, onVencida }: CuentaRegresivaProps): ReactElement {
  const [segundos, setSegundos] = useState<number>(() => segundosRestantes(expiraEn, Date.now()));

  useEffect(() => {
    const interval = window.setInterval(() => {
      const restantes = segundosRestantes(expiraEn, Date.now());
      setSegundos(restantes);
      if (restantes <= 0) {
        window.clearInterval(interval);
        onVencida?.();
      }
    }, 1000);
    return () => window.clearInterval(interval);
  }, [expiraEn, onVencida]);

  const vencida = retencionVencida(expiraEn, Date.now()) || segundos <= 0;

  return (
    <p
      aria-live="polite"
      role={vencida ? "alert" : "status"}
      className={`text-sm font-medium ${vencida ? "text-rose-700" : "text-foreground/80"}`}
    >
      {vencida ? "Se liberó el horario" : `Tu horario se reserva por ${formatearCuentaRegresiva(segundos)}`}
    </p>
  );
}