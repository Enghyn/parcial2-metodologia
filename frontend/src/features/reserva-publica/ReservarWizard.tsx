// Wizard público de reserva (C-06, D9/D14): 4 pasos sin autenticación.
import type { ReactElement } from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { reservar } from "../../shared/api/public";
import type { SlotPublico } from "../../shared/api/public";
import { PasoPrestacion } from "./steps/PasoPrestacion";
import { PasoProfesional } from "./steps/PasoProfesional";
import { PasoHorario } from "./steps/PasoHorario";
import { PasoDatos } from "./steps/PasoDatos";
import { formatFechaUtc, formatHoraUtc } from "./types";
import type { DatosPaciente, Prestacion } from "./types";

export function ReservarWizard(): ReactElement {
  const navigate = useNavigate();
  const [paso, setPaso] = useState<number>(1);
  const [prestacion, setPrestacion] = useState<Prestacion | null>(null);
  const [profesionalId, setProfesionalId] = useState<string | null>(null);
  const [slot, setSlot] = useState<SlotPublico | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState<boolean>(false);

  function elegirPrestacion(elegida: Prestacion): void {
    setPrestacion(elegida);
    setProfesionalId(null);
    setSlot(null);
    setError(null);
    setPaso(2);
  }

  function elegirProfesional(id: string | null): void {
    setProfesionalId(id);
    setSlot(null);
    setError(null);
    setPaso(3);
  }

  function elegirSlot(elegido: SlotPublico): void {
    setSlot(elegido);
    setError(null);
    setPaso(4);
  }

  async function confirmar(paciente: DatosPaciente): Promise<void> {
    if (prestacion === null || slot === null) {
      setError("Faltan datos de la reserva. Volvé a elegir el horario.");
      return;
    }
    setEnviando(true);
    setError(null);
    try {
      const turno = await reservar({
        prestacion: prestacion.nombre,
        duracion_min: prestacion.duracion_min,
        inicio: slot.inicio,
        profesional_id: slot.profesional_id,
        sillon_id: slot.sillon_id,
        paciente: {
          nombre: paciente.nombre.trim(),
          dni: paciente.dni.trim(),
          telefono: paciente.telefono.trim(),
          email: paciente.email.trim() === "" ? null : paciente.email.trim(),
        },
      });
      navigate(`/p/turno/${turno.token}`, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "No pudimos completar la reserva.");
    } finally {
      setEnviando(false);
    }
  }

  const resumen =
    prestacion !== null && slot !== null
      ? `${prestacion.nombre} · ${formatFechaUtc(slot.inicio)} a las ${formatHoraUtc(slot.inicio)}`
      : "";

  return (
    <section className="mx-auto max-w-2xl space-y-6 p-6">
      <header>
        <h1 className="text-2xl font-semibold">Reservá tu turno</h1>
        <p className="text-sm text-foreground/70">
          Elegí el día y la hora que te quede cómoda. Te lo confirmamos por WhatsApp.
        </p>
      </header>

      {error !== null && (
        <p role="alert" className="rounded border border-rose-300 bg-rose-50 p-3 text-sm text-rose-700">
          {error}
        </p>
      )}

      {paso === 1 && <PasoPrestacion onSelect={elegirPrestacion} />}
      {paso === 2 && (
        <PasoProfesional onSelect={elegirProfesional} onBack={() => setPaso(1)} />
      )}
      {paso === 3 && prestacion !== null && (
        <PasoHorario
          duracionMin={prestacion.duracion_min}
          profesionalId={profesionalId}
          onSelect={elegirSlot}
          onBack={() => setPaso(2)}
        />
      )}
      {paso === 4 && (
        <PasoDatos
          resumen={resumen}
          enviando={enviando}
          onBack={() => setPaso(3)}
          onSubmit={(paciente) => void confirmar(paciente)}
        />
      )}
    </section>
  );
}
