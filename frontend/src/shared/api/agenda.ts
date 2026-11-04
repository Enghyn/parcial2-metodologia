// Cliente tipado para agenda (turnos), reusando request<T> de client.ts (R7, R8).
import { request } from "./client";

export type EstadoTurno = "reservado" | "confirmado" | "presente" | "atendido" | "cancelado";

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

export function listarTurnos(filtros: {
  fecha?: string;
  profesional_id?: string;
  sillon_id?: string;
}): Promise<TurnoOut[]> {
  const params = new URLSearchParams();
  if (filtros.fecha !== undefined) params.set("fecha", filtros.fecha);
  if (filtros.profesional_id !== undefined) params.set("profesional_id", filtros.profesional_id);
  if (filtros.sillon_id !== undefined) params.set("sillon_id", filtros.sillon_id);
  const qs = params.toString();
  const path = qs.length > 0 ? `/api/v1/turnos?${qs}` : "/api/v1/turnos";
  return request<TurnoOut[]>(path);
}

export function crearTurno(input: TurnoCreateInput): Promise<TurnoOut> {
  return request<TurnoOut>("/api/v1/turnos", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function cambiarEstadoTurno(id: string, estado: EstadoTurno): Promise<TurnoOut> {
  return request<TurnoOut>(`/api/v1/turnos/${id}/estado`, {
    method: "PATCH",
    body: JSON.stringify({ estado }),
  });
}