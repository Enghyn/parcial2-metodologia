// Cliente tipado de ficha clínica (C-07): pacientes y odontograma FDI.
// `request` se importa de forma diferida para que los tests de node:test
// puedan cargar el módulo sin arrastrar AuthContext/React.
function request<T>(path: string, init?: RequestInit): Promise<T> {
  return import("./client.ts").then(({ request: doRequest }) =>
    doRequest<T>(path, init),
  );
}

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

// ── C-11: Evolución clínica ──────────────────────────────────────────────

export interface Evolucion {
  id: string;
  paciente_id: string;
  autor_usuario_id: string;
  fecha: string;
  texto: string;
}

export interface EvolucionCreateInput {
  texto: string;
}

export function listarEvoluciones(pacienteId: string): Promise<Evolucion[]> {
  return request<Evolucion[]>(`/api/v1/pacientes/${pacienteId}/evoluciones`);
}

export function crearEvolucion(
  pacienteId: string,
  input: EvolucionCreateInput,
): Promise<Evolucion> {
  return request<Evolucion>(`/api/v1/pacientes/${pacienteId}/evoluciones`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

// ── C-11: Consentimiento informado ───────────────────────────────────────

export interface Consentimiento {
  id: string;
  paciente_id: string;
  version: string;
  fecha: string;
  autor_usuario_id: string;
}

export interface ConsentimientoCreateInput {
  version: string;
}

export function listarConsentimientos(pacienteId: string): Promise<Consentimiento[]> {
  return request<Consentimiento[]>(`/api/v1/pacientes/${pacienteId}/consentimientos`);
}

export function crearConsentimiento(
  pacienteId: string,
  input: ConsentimientoCreateInput,
): Promise<Consentimiento> {
  return request<Consentimiento>(`/api/v1/pacientes/${pacienteId}/consentimientos`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

// ── C-11: Historial por pieza ────────────────────────────────────────────

export interface HistorialPieza {
  estado_anterior: string | null;
  estado_nuevo: string;
  observacion_anterior: string | null;
  observacion_nueva: string | null;
  registrado_en: string;
  registrado_por: string | null;
}

export function getHistorialPieza(
  pacienteId: string,
  pieza: number,
): Promise<HistorialPieza[]> {
  return request<HistorialPieza[]>(
    `/api/v1/pacientes/${pacienteId}/odontograma/piezas/${pieza}/historial`,
  );
}
