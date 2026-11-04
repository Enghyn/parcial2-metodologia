// Cliente tipado del portal público (C-06), reusando request<T> de client.ts (R7).
import { request } from "./client";

export interface SlotPublico {
  inicio: string;
  profesional_id: string;
  sillon_id: string;
}

export interface ProfesionalPublico {
  id: string;
  nombre: string;
}

export interface PacientePublicoInput {
  nombre: string;
  dni: string;
  telefono: string;
  email?: string | null;
}

export interface ReservaPublicaInput {
  prestacion: string;
  duracion_min: number;
  inicio: string;
  profesional_id: string;
  sillon_id: string;
  paciente: PacientePublicoInput;
}

export interface TurnoPublicoOut {
  token: string;
  prestacion: string;
  inicio: string;
  fin: string;
  duracion_min: number;
  estado: string;
  paciente_nombre: string;
  profesional_nombre: string;
  sillon_nombre: string;
}

export function getDisponibilidad(params: {
  fecha: string;
  duracion_min: number;
  profesional_id?: string;
}): Promise<SlotPublico[]> {
  const qs = new URLSearchParams();
  qs.set("fecha", params.fecha);
  qs.set("duracion_min", String(params.duracion_min));
  if (params.profesional_id !== undefined) {
    qs.set("profesional_id", params.profesional_id);
  }
  return request<SlotPublico[]>(`/api/v1/public/disponibilidad?${qs.toString()}`);
}

export function listarProfesionalesPublicos(): Promise<ProfesionalPublico[]> {
  return request<ProfesionalPublico[]>("/api/v1/public/profesionales");
}

export function reservar(input: ReservaPublicaInput): Promise<TurnoPublicoOut> {
  return request<TurnoPublicoOut>("/api/v1/public/reservar", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function getTurnoPublico(token: string): Promise<TurnoPublicoOut> {
  return request<TurnoPublicoOut>(`/api/v1/public/turnos/${token}`);
}

export function cancelarTurnoPublico(token: string): Promise<TurnoPublicoOut> {
  return request<TurnoPublicoOut>(`/api/v1/public/turnos/${token}/cancelar`, {
    method: "POST",
  });
}
