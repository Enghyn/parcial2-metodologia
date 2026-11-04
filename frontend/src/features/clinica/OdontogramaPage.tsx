// Odontograma FDI interactivo (C-07): 32 piezas, 4 cuadrantes y upsert por pieza.
import type { ReactElement } from "react";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuthStore } from "../../app/AuthContext";
import { getOdontograma, listarPacientes, upsertPieza } from "../../shared/api/clinica";
import type { EstadoPieza, Hallazgo, Odontograma } from "../../shared/api/clinica";
import { CUADRANTES_FDI } from "./piezas";

const ESTADOS: { value: EstadoPieza; label: string; clase: string }[] = [
  { value: "sano", label: "Sano", clase: "bg-emerald-50 text-emerald-800 border-emerald-300" },
  { value: "caries", label: "Caries", clase: "bg-amber-50 text-amber-800 border-amber-300" },
  { value: "obturacion", label: "Obturación", clase: "bg-sky-50 text-sky-800 border-sky-300" },
  { value: "corona", label: "Corona", clase: "bg-violet-50 text-violet-800 border-violet-300" },
  { value: "extraccion", label: "Extracción", clase: "bg-rose-50 text-rose-800 border-rose-300" },
  {
    value: "tratamiento_conducto",
    label: "Tratamiento de conducto",
    clase: "bg-orange-50 text-orange-800 border-orange-300",
  },
];

const ESTADO_POR_DEFECTO: EstadoPieza = "sano";

function infoEstado(estado: EstadoPieza) {
  return ESTADOS.find((e) => e.value === estado) ?? ESTADOS[0];
}

export function OdontogramaPage(): ReactElement {
  const { pacienteId } = useParams<{ pacienteId: string }>();
  const user = useAuthStore((s) => s.user);
  const [odontograma, setOdontograma] = useState<Odontograma | null>(null);
  const [pacienteNombre, setPacienteNombre] = useState<string>("");
  const [seleccionada, setSeleccionada] = useState<number | null>(null);
  const [estado, setEstado] = useState<EstadoPieza>(ESTADO_POR_DEFECTO);
  const [observacion, setObservacion] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [guardando, setGuardando] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const canEdit = user?.rol === "odontologo";

  const hallazgos = useMemo(() => {
    const mapa = new Map<number, Hallazgo>();
    odontograma?.hallazgos.forEach((h) => mapa.set(h.pieza, h));
    return mapa;
  }, [odontograma]);

  useEffect(() => {
    if (pacienteId === undefined) {
      setError("Falta el paciente.");
      setLoading(false);
      return;
    }
    let activo = true;
    setLoading(true);
    Promise.all([getOdontograma(pacienteId), listarPacientes()])
      .then(([od, pacientes]) => {
        if (!activo) return;
        setOdontograma(od);
        setPacienteNombre(pacientes.find((p) => p.id === pacienteId)?.nombre ?? "Paciente");
      })
      .catch(() => {
        if (activo) setError("No pudimos cargar el odontograma.");
      })
      .finally(() => {
        if (activo) setLoading(false);
      });
    return () => {
      activo = false;
    };
  }, [pacienteId]);

  function seleccionar(pieza: number): void {
    const hallazgo = hallazgos.get(pieza);
    setSeleccionada(pieza);
    setEstado(hallazgo?.estado ?? ESTADO_POR_DEFECTO);
    setObservacion(hallazgo?.observacion ?? "");
  }

  async function guardar(): Promise<void> {
    if (pacienteId === undefined || seleccionada === null || !canEdit) return;
    setGuardando(true);
    setError(null);
    try {
      await upsertPieza(pacienteId, seleccionada, {
        estado,
        observacion: observacion.trim() === "" ? null : observacion.trim(),
      });
      setOdontograma(await getOdontograma(pacienteId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "No pudimos guardar la pieza.");
    } finally {
      setGuardando(false);
    }
  }

  return (
    <section className="space-y-4 p-4">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <Link to="/app/pacientes" className="text-sm underline">
            ← Pacientes
          </Link>
          <h1 className="text-xl font-semibold">Odontograma · {pacienteNombre}</h1>
          <p className="text-sm text-foreground/70">
            {canEdit ? "Seleccioná una pieza para editarla." : "Vista de lectura."}
          </p>
        </div>
        {odontograma !== null && (
          <p className="text-xs text-foreground/50">
            {odontograma.hallazgos.length} pieza
            {odontograma.hallazgos.length === 1 ? "" : "s"} con hallazgos
          </p>
        )}
      </header>

      {loading && <p className="text-sm text-foreground/60">Cargando odontograma...</p>}
      {error !== null && <p className="text-sm text-rose-600">{error}</p>}

      <div className="space-y-3">
        {CUADRANTES_FDI.map((cuadrante) => (
          <div key={cuadrante.titulo} className="rounded border border-border p-3">
            <h2 className="mb-2 text-sm font-semibold">{cuadrante.titulo}</h2>
            <div className="grid grid-cols-8 gap-1">
              {cuadrante.piezas.map((pieza) => {
                const hallazgo = hallazgos.get(pieza);
                const info = infoEstado(hallazgo?.estado ?? ESTADO_POR_DEFECTO);
                const activa = seleccionada === pieza;
                return (
                  <button
                    key={pieza}
                    type="button"
                    onClick={() => seleccionar(pieza)}
                    className={`rounded border p-1 text-center text-xs ${info.clase} ${
                      activa ? "ring-2 ring-primary" : ""
                    }`}
                    title={`Pieza ${pieza}: ${info.label}`}
                  >
                    <span className="block font-semibold">{pieza}</span>
                    <span className="block text-[10px]">{info.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {seleccionada !== null && (
        <div className="rounded border border-border p-3">
          <h2 className="text-sm font-semibold">Pieza {seleccionada}</h2>
          <div className="mt-2 grid gap-2 sm:grid-cols-2">
            <label className="block text-sm">
              Estado
              <select
                value={estado}
                disabled={!canEdit}
                onChange={(event) => setEstado(event.target.value as EstadoPieza)}
                className="mt-1 w-full rounded border border-border px-3 py-2"
              >
                {ESTADOS.map((opcion) => (
                  <option key={opcion.value} value={opcion.value}>
                    {opcion.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm">
              Observación
              <input
                value={observacion}
                disabled={!canEdit}
                onChange={(event) => setObservacion(event.target.value)}
                maxLength={255}
                className="mt-1 w-full rounded border border-border px-3 py-2"
                placeholder="Nota breve (opcional)"
              />
            </label>
          </div>
          {canEdit && (
            <button
              type="button"
              onClick={() => void guardar()}
              disabled={guardando}
              className="mt-2 rounded bg-primary px-4 py-2 text-primary-foreground disabled:opacity-60"
            >
              {guardando ? "Guardando..." : "Guardar pieza"}
            </button>
          )}
        </div>
      )}
    </section>
  );
}
