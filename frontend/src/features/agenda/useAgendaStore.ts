// Store de agenda (Zustand) con carga paralela (D2).
import { create } from "zustand";
import {
  cambiarEstadoTurno,
  crearSobreturno,
  crearTurno,
  listarTurnos,
  reprogramarTurno,
} from "../../shared/api/agenda";
import type {
  EstadoTurno,
  ReprogramarInput,
  TurnoCreateInput,
  TurnoOut,
} from "../../shared/api/agenda";
import { cargarCatalogos } from "./catalogos";
import type { Sillon, Profesional, Paciente } from "./types";

interface AgendaState {
  fechaSeleccionada: string;
  semana: { desde: string; hasta: string } | null;
  turnos: TurnoOut[];
  sillones: Sillon[];
  profesionales: Profesional[];
  pacientes: Paciente[];
  loading: boolean;
  error: string | null;
  errorCarga: string | null;
  cargar: (fecha: string) => Promise<void>;
  cargarSemana: (desde: string, hasta: string) => Promise<void>;
  crear: (datos: TurnoCreateInput) => Promise<TurnoOut>;
  crearSobreturno: (datos: TurnoCreateInput, motivo: string) => Promise<TurnoOut>;
  reprogramar: (id: string, datos: ReprogramarInput) => Promise<void>;
  cambiarEstado: (id: string, estado: EstadoTurno) => Promise<void>;
}

function mensajeError(err: unknown): string {
  if (err instanceof Error) return err.message;
  return "Error inesperado";
}

export const useAgendaStore = create<AgendaState>()((set) => ({
  fechaSeleccionada: "",
  semana: null,
  turnos: [],
  sillones: [],
  profesionales: [],
  pacientes: [],
  loading: false,
  error: null,
  errorCarga: null,
  cargar: async (fecha: string): Promise<void> => {
    set({ loading: true, error: null, errorCarga: null });
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
      const mensaje = mensajeError(err);
      set({ error: mensaje, errorCarga: mensaje, loading: false });
    }
  },
  cargarSemana: async (desde: string, hasta: string): Promise<void> => {
    set({ loading: true, error: null, errorCarga: null });
    try {
      // Una sola consulta de turnos para los siete días (D11).
      const [catalogos, turnos] = await Promise.all([
        cargarCatalogos(),
        listarTurnos({ desde, hasta }),
      ]);
      set({
        semana: { desde, hasta },
        turnos,
        sillones: catalogos.sillones,
        profesionales: catalogos.profesionales,
        pacientes: catalogos.pacientes,
        loading: false,
      });
    } catch (err) {
      const mensaje = mensajeError(err);
      set({ error: mensaje, errorCarga: mensaje, loading: false });
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
  crearSobreturno: async (datos: TurnoCreateInput, motivo: string): Promise<TurnoOut> => {
    set({ loading: true, error: null });
    try {
      const turno = await crearSobreturno(datos, motivo);
      set((s) => ({ turnos: [...s.turnos, turno], loading: false }));
      return turno;
    } catch (err) {
      set({ error: mensajeError(err), loading: false });
      throw err;
    }
  },
  reprogramar: async (id: string, datos: ReprogramarInput): Promise<void> => {
    set({ loading: true, error: null });
    try {
      const actualizado = await reprogramarTurno(id, datos);
      set((s) => ({
        turnos: s.turnos.map((t) => (t.id === id ? actualizado : t)),
        loading: false,
      }));
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