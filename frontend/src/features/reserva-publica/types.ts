// Tipos y catálogo estático del wizard público (C-06, D9; sin `any`, R7).
import type { SlotPublico } from "../../shared/api/public";

export { formatFecha, formatHora, toIsoDate } from "../../shared/date";

export interface Prestacion {
  nombre: string;
  duracion_min: number;
}

// Catálogo estático: la duración no vive aún en un catálogo persistido (KB 10).
export const PRESTACIONES: Prestacion[] = [
  { nombre: "Consulta diagnóstica", duracion_min: 30 },
  { nombre: "Limpieza", duracion_min: 30 },
  { nombre: "Extracción", duracion_min: 60 },
  { nombre: "Endodoncia", duracion_min: 60 },
  { nombre: "Control de ortodoncia", duracion_min: 30 },
];

export interface DatosPaciente {
  nombre: string;
  dni: string;
  telefono: string;
  email: string;
}

export interface SeleccionReserva {
  prestacion: Prestacion | null;
  profesionalId: string | null;
  slot: SlotPublico | null;
}
