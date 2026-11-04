// Modal de alta de turno.
import type { ReactElement, FormEvent } from "react";
import { useEffect, useState } from "react";
import type { Catalogos } from "./types";
import type { TurnoCreateInput } from "../../shared/api/agenda";

interface TurnoModalProps {
  open: boolean;
  catalogos: Catalogos;
  onClose: () => void;
  onCrear: (input: TurnoCreateInput) => Promise<void>;
}

interface FormState {
  paciente_id: string;
  profesional_id: string;
  sillon_id: string;
  prestacion: string;
  inicio: string;
  duracion_min: string;
  sena_monto: string;
  notas: string;
}

const EMPTY: FormState = {
  paciente_id: "",
  profesional_id: "",
  sillon_id: "",
  prestacion: "",
  inicio: "",
  duracion_min: "30",
  sena_monto: "0",
  notas: "",
};

export function TurnoModal({ open, catalogos, onClose, onCrear }: TurnoModalProps): ReactElement | null {
  const [form, setForm] = useState<FormState>(EMPTY);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    if (open) {
      setForm(EMPTY);
      setError(null);
      setPending(false);
    }
  }, [open]);

  if (!open) return null;

  function update<K extends keyof FormState>(key: K, value: FormState[K]): void {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    if (
      form.paciente_id === "" ||
      form.profesional_id === "" ||
      form.sillon_id === "" ||
      form.prestacion.trim() === "" ||
      form.inicio === "" ||
      Number(form.duracion_min) <= 0
    ) {
      setError("Completá todos los campos requeridos.");
      return;
    }
    setPending(true);
    try {
      const isoInicio = new Date(form.inicio).toISOString();
      const input: TurnoCreateInput = {
        paciente_id: form.paciente_id,
        profesional_id: form.profesional_id,
        sillon_id: form.sillon_id,
        prestacion: form.prestacion.trim(),
        inicio: isoInicio,
        duracion_min: Number(form.duracion_min),
        sena_monto: form.sena_monto,
        notas: form.notas.trim() === "" ? null : form.notas.trim(),
      };
      await onCrear(input);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear el turno");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-lg rounded bg-background p-6 shadow-lg">
        <h2 className="text-lg font-semibold">Nuevo turno</h2>
        <form onSubmit={(e) => void handleSubmit(e)} className="mt-4 space-y-3">
          <div>
            <label className="block text-sm font-medium">Paciente</label>
            <select
              value={form.paciente_id}
              onChange={(e) => update("paciente_id", e.target.value)}
              className="w-full rounded border border-border px-3 py-2"
            >
              <option value="">Seleccioná...</option>
              {catalogos.pacientes.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nombre}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium">Profesional</label>
            <select
              value={form.profesional_id}
              onChange={(e) => update("profesional_id", e.target.value)}
              className="w-full rounded border border-border px-3 py-2"
            >
              <option value="">Seleccioná...</option>
              {catalogos.profesionales.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nombre}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium">Sillón</label>
            <select
              value={form.sillon_id}
              onChange={(e) => update("sillon_id", e.target.value)}
              className="w-full rounded border border-border px-3 py-2"
            >
              <option value="">Seleccioná...</option>
              {catalogos.sillones.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nombre}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium">Prestación</label>
            <input
              type="text"
              value={form.prestacion}
              onChange={(e) => update("prestacion", e.target.value)}
              className="w-full rounded border border-border px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium">Inicio</label>
            <input
              type="datetime-local"
              value={form.inicio}
              onChange={(e) => update("inicio", e.target.value)}
              className="w-full rounded border border-border px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium">Duración (min)</label>
            <input
              type="number"
              min={1}
              value={form.duracion_min}
              onChange={(e) => update("duracion_min", e.target.value)}
              className="w-full rounded border border-border px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium">Seña (ARS)</label>
            <input
              type="text"
              value={form.sena_monto}
              onChange={(e) => update("sena_monto", e.target.value)}
              className="w-full rounded border border-border px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium">Notas</label>
            <textarea
              value={form.notas}
              onChange={(e) => update("notas", e.target.value)}
              className="w-full rounded border border-border px-3 py-2"
            />
          </div>
          {error !== null && <p className="text-sm text-rose-600">{error}</p>}
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded border border-border px-4 py-2"
              disabled={pending}
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={pending}
              className="rounded bg-primary px-4 py-2 text-primary-foreground disabled:opacity-60"
            >
              {pending ? "Guardando..." : "Crear"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}