// Cliente tipado de ficha clínica (C-07): pacientes y odontograma FDI.
import { request } from "./client";

export type EstadoPieza =
  | "sano"
  | "caries"
  | "obturacion"
  | "corona"
  | "extraccion"
  | "tratamiento_conducto";

export interface Paciente {
  id: string;
  nombre: string;
  dni: string;
  telefono: string;
  email: string | null;
  obra_social: string | null;
  nro_afiliado: string | null;
  activo: boolean;
}

export interface PacienteCreateInput {
  nombre: string;
  dni: string;
  telefono: string;
  email?: string | null;
  obra_social?: string | null;
  nro_afiliado?: string | null;
}

export interface Hallazgo {
  pieza: number;
  estado: EstadoPieza;
  observacion: string | null;
  fecha: string;
}

export interface Odontograma {
  id: string;
  paciente_id: string;
  observaciones_generales: string | null;
  hallazgos: Hallazgo[];
}

export interface HallazgoInput {
  estado: EstadoPieza;
  observacion?: string | null;
  fecha?: string;
}

export function listarPacientes(q?: string): Promise<Paciente[]> {
  const params = new URLSearchParams();
  if (q !== undefined && q.trim() !== "") {
    params.set("q", q.trim());
  }
  const qs = params.toString();
  return request<Paciente[]>(`/api/v1/pacientes${qs === "" ? "" : `?${qs}`}`);
}

export function crearPaciente(input: PacienteCreateInput): Promise<Paciente> {
  return request<Paciente>("/api/v1/pacientes", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function getOdontograma(pacienteId: string): Promise<Odontograma> {
  return request<Odontograma>(`/api/v1/pacientes/${pacienteId}/odontograma`);
}

export function upsertPieza(
  pacienteId: string,
  pieza: number,
  input: HallazgoInput,
): Promise<Hallazgo> {
  return request<Hallazgo>(
    `/api/v1/pacientes/${pacienteId}/odontograma/piezas/${pieza}`,
    {
      method: "PUT",
      body: JSON.stringify(input),
    },
  );
}
