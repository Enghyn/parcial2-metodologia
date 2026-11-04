// Directorio de pacientes: búsqueda, alta y acceso al odontograma.
import type { FormEvent, ReactElement } from "react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuthStore } from "../../app/AuthContext";
import { crearPaciente, listarPacientes } from "../../shared/api/clinica";
import type { Paciente } from "../../shared/api/clinica";

const FORM_INICIAL = {
  nombre: "",
  dni: "",
  telefono: "",
  email: "",
  obra_social: "",
};

export function PacientesPage(): ReactElement {
  const user = useAuthStore((s) => s.user);
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [q, setQ] = useState<string>("");
  const [recarga, setRecarga] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState<boolean>(false);
  const [form, setForm] = useState(FORM_INICIAL);
  const [guardando, setGuardando] = useState<boolean>(false);

  const canCreate = user?.rol === "admin" || user?.rol === "recepcion";

  useEffect(() => {
    let activo = true;
    setLoading(true);
    setError(null);
    listarPacientes(q)
      .then((data) => {
        if (activo) setPacientes(data);
      })
      .catch(() => {
        if (activo) setError("No pudimos cargar los pacientes.");
      })
      .finally(() => {
        if (activo) setLoading(false);
      });
    return () => {
      activo = false;
    };
  }, [q, recarga]);

  function actualizar(campo: keyof typeof FORM_INICIAL, valor: string): void {
    setForm((actual) => ({ ...actual, [campo]: valor }));
  }

  async function handleCrear(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    if (form.nombre.trim() === "" || form.dni.trim() === "" || form.telefono.trim() === "") {
      setError("Nombre, DNI y teléfono son obligatorios.");
      return;
    }
    setGuardando(true);
    try {
      await crearPaciente({
        nombre: form.nombre.trim(),
        dni: form.dni.trim(),
        telefono: form.telefono.trim(),
        email: form.email.trim() === "" ? null : form.email.trim(),
        obra_social: form.obra_social.trim() === "" ? null : form.obra_social.trim(),
      });
      setForm(FORM_INICIAL);
      setFormOpen(false);
      setRecarga((n) => n + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No pudimos crear el paciente.");
    } finally {
      setGuardando(false);
    }
  }

  return (
    <section className="space-y-4 p-4">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold">Pacientes</h1>
          <p className="text-sm text-foreground/70">
            {pacientes.length} paciente{pacientes.length === 1 ? "" : "s"} activo
            {pacientes.length === 1 ? "" : "s"}
          </p>
        </div>
        {canCreate && (
          <button
            type="button"
            onClick={() => setFormOpen((abierto) => !abierto)}
            className="rounded bg-primary px-4 py-2 text-primary-foreground"
          >
            {formOpen ? "Cancelar" : "Nuevo paciente"}
          </button>
        )}
      </header>

      <label className="block text-sm font-medium">
        Buscar por nombre o DNI
        <input
          type="search"
          value={q}
          onChange={(event) => setQ(event.target.value)}
          className="mt-1 w-full rounded border border-border px-3 py-2"
          placeholder="Ej.: 30111222 o Pérez"
        />
      </label>

      {error !== null && <p className="text-sm text-rose-600">{error}</p>}
      {loading && <p className="text-sm text-foreground/60">Cargando pacientes...</p>}

      {formOpen && canCreate && (
        <form onSubmit={(event) => void handleCrear(event)} className="space-y-2 rounded border border-border p-4">
          <div className="grid gap-2 sm:grid-cols-2">
            <input
              value={form.nombre}
              onChange={(event) => actualizar("nombre", event.target.value)}
              placeholder="Nombre completo"
              className="rounded border border-border px-3 py-2"
              required
            />
            <input
              value={form.dni}
              onChange={(event) => actualizar("dni", event.target.value)}
              placeholder="DNI"
              className="rounded border border-border px-3 py-2"
              required
            />
            <input
              value={form.telefono}
              onChange={(event) => actualizar("telefono", event.target.value)}
              placeholder="Teléfono"
              className="rounded border border-border px-3 py-2"
              required
            />
            <input
              value={form.email}
              onChange={(event) => actualizar("email", event.target.value)}
              placeholder="Email (opcional)"
              className="rounded border border-border px-3 py-2"
            />
            <input
              value={form.obra_social}
              onChange={(event) => actualizar("obra_social", event.target.value)}
              placeholder="Obra social (opcional)"
              className="rounded border border-border px-3 py-2"
            />
          </div>
          <button
            type="submit"
            disabled={guardando}
            className="rounded bg-primary px-4 py-2 text-primary-foreground disabled:opacity-60"
          >
            {guardando ? "Guardando..." : "Guardar paciente"}
          </button>
        </form>
      )}

      <div className="overflow-x-auto rounded border border-border">
        <table className="w-full text-left text-sm">
          <thead className="bg-muted/40">
            <tr>
              <th className="px-3 py-2">Nombre</th>
              <th className="px-3 py-2">DNI</th>
              <th className="px-3 py-2">Teléfono</th>
              <th className="px-3 py-2">Obra social</th>
              <th className="px-3 py-2">Ficha</th>
            </tr>
          </thead>
          <tbody>
            {pacientes.map((paciente) => (
              <tr key={paciente.id} className="border-t border-border">
                <td className="px-3 py-2">{paciente.nombre}</td>
                <td className="px-3 py-2">{paciente.dni}</td>
                <td className="px-3 py-2">{paciente.telefono}</td>
                <td className="px-3 py-2">{paciente.obra_social ?? "—"}</td>
                <td className="px-3 py-2">
                  <Link to={`/app/odontograma/${paciente.id}`} className="underline">
                    Abrir odontograma
                  </Link>
                </td>
              </tr>
            ))}
            {pacientes.length === 0 && !loading && (
              <tr>
                <td colSpan={5} className="px-3 py-4 text-center text-foreground/60">
                  No hay pacientes para mostrar.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
