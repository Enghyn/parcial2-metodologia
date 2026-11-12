// Firma simple del presupuesto (C-18, task 5.1): nombre del paciente + aprobación.
// La firma en blanco no habilita el envío (`puedeEnviarFirma`, testeado puro).
import type { FormEvent, ReactElement } from "react";
import { puedeEnviarFirma } from "./presentacion";

interface FirmaSimpleProps {
  firma: string;
  onCambiarFirma: (valor: string) => void;
  onAprobar: () => void;
  enviando: boolean;
}

export function FirmaSimple({
  firma,
  onCambiarFirma,
  onAprobar,
  enviando,
}: FirmaSimpleProps): ReactElement {
  const habilitado = puedeEnviarFirma(firma) && !enviando;

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (habilitado) {
      onAprobar();
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2 rounded border border-border p-4">
      <label className="block text-sm font-medium" htmlFor="firma-presupuesto">
        Firmá con tu nombre y apellido
      </label>
      <input
        id="firma-presupuesto"
        type="text"
        value={firma}
        onChange={(event) => onCambiarFirma(event.target.value)}
        placeholder="Ej.: Ana Pérez"
        className="w-full rounded border border-border px-3 py-2"
      />
      <button
        type="submit"
        disabled={!habilitado}
        className="rounded bg-primary px-4 py-2 text-primary-foreground disabled:opacity-60"
      >
        {enviando ? "Aprobando..." : "Aprobar presupuesto"}
      </button>
    </form>
  );
}
