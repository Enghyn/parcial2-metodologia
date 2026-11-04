// Store de agenda (Zustand) con carga paralela (D2).
import { create } from "zustand";
import { listarTurnos, crearTurno, cambiarEstadoTurno } from "../../shared/api/agenda";
import type { TurnoCreateInput, TurnoOut, EstadoTurno } from "../../shared/api/agenda";
import { cargarCatalogos } from "./catalogos";
import type { Sillon, Profesional, Paciente } from "./types";

interface AgendaState {
  fechaSeleccionada: string;
  turnos: TurnoOut[];
  sillones: Sillon[];
  profesionales: Profesional[];
  pacientes: Paciente[];
  loading: boolean;
  error: string | null;
  cargar: (fecha: string) => Promise<void>;
  crear: (datos: TurnoCreateInput) => Promise<TurnoOut>;
  cambiarEstado: (id: string, estado: EstadoTurno) => Promise<void>;
}

function mensajeError(err: unknown): string {
  if (err instanceof Error) return err.message;
  return "Error inesperado";
}

export const useAgendaStore = create<AgendaState>()((set) => ({
  fechaSeleccionada: "",
  turnos: [],
  sillones: [],
  profesionales: [],
  pacientes: [],
  loading: false,
  error: null,
  cargar: async (fecha: string): Promise<void> => {
    set({ loading: true, error: null });
    try {
      const [catalogos, turnos] = await Promise.all([cargarCatalogos(), listarTurnos({ fecha })]);
      set({
        fechaSeleccionada: fecha,
        turnos,
        sillones: catalogos.sillones,
        profesionales: catalogos.profesionales,
        pacientes: catalogos.pacientes,
        loading: false,
      });
    } catch (err) {
      set({ error: mensajeError(err), loading: false });
    }
  },
  crear: async (datos: TurnoCreateInput): Promise<TurnoOut> => {
    set({ loading: true, error: null });
    try {
      const turno = await crearTurno(datos);
      set((s) => ({ turnos: [...s.turnos, turno], loading: false }));
      return turno;
    } catch (err) {
      set({ error: mensajeError(err), loading: false });
      throw err;
    }
  },
  cambiarEstado: async (id: string, estado: EstadoTurno): Promise<void> => {
    set({ loading: true, error: null });
    try {
      const actualizado = await cambiarEstadoTurno(id, estado);
      set((s) => ({
        turnos: s.turnos.map((t) => (t.id === id ? actualizado : t)),
        loading: false,
      }));
    } catch (err) {
      set({ error: mensajeError(err), loading: false });
    }
  },
}));