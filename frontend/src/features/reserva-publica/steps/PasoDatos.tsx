// Paso 4 del wizard: datos del paciente y confirmación de la reserva.
import type { FormEvent, ReactElement } from "react";
import { useState } from "react";
import type { DatosPaciente } from "../types";

interface PasoDatosProps {
  resumen: string;
  enviando: boolean;
  onBack: () => void;
  onSubmit: (paciente: DatosPaciente) => void;
}

const VACIO: DatosPaciente = { nombre: "", dni: "", telefono: "", email: "" };

export function PasoDatos({ resumen, enviando, onBack, onSubmit }: PasoDatosProps): ReactElement {
  const [form, setForm] = useState<DatosPaciente>(VACIO);

  function update<K extends keyof DatosPaciente>(key: K, value: DatosPaciente[K]): void {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    onSubmit(form);
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">4. Tus datos</h2>
      <p className="rounded bg-foreground/5 p-3 text-sm">{resumen}</p>
      <form onSubmit={handleSubmit} className="space-y-3">
        <label className="block text-sm font-medium">
          Nombre y apellido
          <input
            type="text"
            required
            maxLength={100}
            value={form.nombre}
            onChange={(event) => update("nombre", event.target.value)}
            className="mt-1 w-full rounded border border-border px-3 py-2"
          />
        </label>
        <label className="block text-sm font-medium">
          DNI
          <input
            type="text"
            required
            maxLength={20}
            value={form.dni}
            onChange={(event) => update("dni", event.target.value)}
            className="mt-1 w-full rounded border border-border px-3 py-2"
          />
        </label>
        <label className="block text-sm font-medium">
          Teléfono
          <input
            type="tel"
            required
            maxLength={30}
            value={form.telefono}
            onChange={(event) => update("telefono", event.target.value)}
            className="mt-1 w-full rounded border border-border px-3 py-2"
          />
        </label>
        <label className="block text-sm font-medium">
          Email (opcional)
          <input
            type="email"
            maxLength={150}
            value={form.email}
            onChange={(event) => update("email", event.target.value)}
            className="mt-1 w-full rounded border border-border px-3 py-2"
          />
        </label>
        <div className="flex items-center justify-between gap-2">
          <button type="button" onClick={onBack} className="text-sm underline" disabled={enviando}>
            Volver
          </button>
          <button
            type="submit"
            disabled={enviando}
            className="rounded bg-primary px-4 py-2 text-primary-foreground disabled:opacity-60"
          >
            {enviando ? "Reservando..." : "Confirmar reserva"}
          </button>
        </div>
      </form>
    </div>
  );
}
