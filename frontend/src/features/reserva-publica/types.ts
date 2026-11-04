// Tipos y catálogo estático del wizard público (C-06, D9; sin `any`, R7).
import type { SlotPublico } from "../../shared/api/public";

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

export function toIsoDate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

// La agenda pública trabaja en UTC por contrato de C-04 (supuesto documentado).
export function formatHoraUtc(iso: string): string {
  return new Date(iso).toLocaleTimeString("es-AR", {
    timeZone: "UTC",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatFechaUtc(iso: string): string {
  return new Date(iso).toLocaleDateString("es-AR", {
    timeZone: "UTC",
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}
