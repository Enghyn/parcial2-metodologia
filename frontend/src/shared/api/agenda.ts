// Cliente tipado para agenda (turnos), reusando request<T> de client.ts (R7, R8).
import { request } from "./client";
import { rutaTurnos } from "./turnosQuery";
import type { FiltroTurnosQuery } from "./turnosQuery";

export type { FiltroTurnosQuery } from "./turnosQuery";
export { construirQueryTurnos, rutaTurnos } from "./turnosQuery";

export type EstadoTurno = "reservado" | "confirmado" | "presente" | "atendido" | "cancelado" | "ausente";

export interface TurnoOut {
  id: string;
  paciente_id: string;
  profesional_id: string;
  sillon_id: string;
  prestacion: string;
  inicio: string;
  fin: string;
  duracion_min: number;
  estado: EstadoTurno;
  token_publico: string;
  sena_monto: string;
  notas: string | null;
  es_sobreturno: boolean;
  motivo_sobreturno: string | null;
  autorizado_por: string | null;
  created_at: string;
  updated_at: string;
}

export interface TurnoCreateInput {
  paciente_id: string;
  profesional_id: string;
  sillon_id: string;
  prestacion: string;
  inicio: string;
  duracion_min: number;
  sena_monto?: string;
  notas?: string | null;
}

export interface ReprogramarInput {
  inicio: string;
  duracion_min?: number;
}

export function listarTurnos(filtros: FiltroTurnosQuery): Promise<TurnoOut[]> {
  return request<TurnoOut[]>(rutaTurnos(filtros));
}

export function crearTurno(input: TurnoCreateInput): Promise<TurnoOut> {
  return request<TurnoOut>("/api/v1/turnos", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function crearSobreturno(input: TurnoCreateInput, motivo: string): Promise<TurnoOut> {
  return request<TurnoOut>("/api/v1/turnos/sobreturno", {
    method: "POST",
    body: JSON.stringify({ ...input, motivo_sobreturno: motivo }),
  });
}

export function reprogramarTurno(id: string, input: ReprogramarInput): Promise<TurnoOut> {
  return request<TurnoOut>(`/api/v1/turnos/${id}/reprogramar`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function cambiarEstadoTurno(id: string, estado: EstadoTurno): Promise<TurnoOut> {
  return request<TurnoOut>(`/api/v1/turnos/${id}/estado`, {
    method: "PATCH",
    body: JSON.stringify({ estado }),
  });
}