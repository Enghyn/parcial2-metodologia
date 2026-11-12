// Cliente tipado del portal público (C-06), reusando request<T> de client.ts (R7).
// `request` se carga de forma diferida para que los helpers puros de este
// módulo (rutas/constructores) puedan importarse en tests de node:test sin
// arrastrar el cliente React/AuthContext.

function request<T>(path: string, init?: RequestInit): Promise<T> {
  return import("./client.ts").then(({ request: doRequest }) => doRequest<T>(path, init));
}

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
  pre_reserva_token?: string | null;
}

export interface PreReservaInput {
  prestacion: string;
  duracion_min: number;
  inicio: string;
  profesional_id: string;
  sillon_id: string;
}

export interface PreReservaOut {
  pre_reserva_token: string;
  inicio: string;
  fin: string;
  duracion_min: number;
  expira_en: string;
}

export interface ReprogramarPublicoInput {
  inicio: string;
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

export function rutaQrReserva(): string {
  return "/api/v1/public/qr/reserva.svg";
}

export function rutaQrTurno(token: string): string {
  return `/api/v1/public/turnos/${token}/qr.svg`;
}

export function construirPreReserva(input: PreReservaInput): PreReservaInput {
  return {
    prestacion: input.prestacion,
    duracion_min: input.duracion_min,
    inicio: input.inicio,
    profesional_id: input.profesional_id,
    sillon_id: input.sillon_id,
  };
}

export function crearPreReserva(input: PreReservaInput): Promise<PreReservaOut> {
  return request<PreReservaOut>("/api/v1/public/pre-reservas", {
    method: "POST",
    body: JSON.stringify(construirPreReserva(input)),
  });
}

export function reprogramarTurnoPublico(token: string, input: ReprogramarPublicoInput): Promise<TurnoPublicoOut> {
  return request<TurnoPublicoOut>(`/api/v1/public/turnos/${token}/reprogramar`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

// --- Portal público de presupuestos y pagos (C-18, D5/D7) ---
// Contratos espejo de `app/modules/public/schemas.py`: sin `id`, `paciente_id`,
// `presupuesto_id`, `movimiento_id` ni `token_publico` (R9). El token opaco viaja
// solo en el path; nunca en query string ni en logs (R9).

export interface ItemPresupuestoPublico {
  descripcion: string;
  cantidad: number;
  arancel: number;
  copago: number;
}

export interface PresupuestoPublico {
  estado: string;
  total: number;
  items: ItemPresupuestoPublico[];
}

export interface PagoPublico {
  estado: string;
  monto: number;
  confirmado_en: string | null;
}

export interface AprobacionPublicaInput {
  firma: string;
}

export interface RechazoPublicoInput {
  motivo?: string | null;
}

export function rutaPresupuestoPublico(token: string): string {
  return `/api/v1/public/presupuestos/${token}`;
}

export function rutaAprobarPresupuestoPublico(token: string): string {
  return `/api/v1/public/presupuestos/${token}/aprobar`;
}

export function rutaRechazarPresupuestoPublico(token: string): string {
  return `/api/v1/public/presupuestos/${token}/rechazar`;
}

export function rutaPagoPublico(token: string): string {
  return `/api/v1/public/pagos/${token}`;
}

export function rutaConfirmarPagoPublico(token: string): string {
  return `/api/v1/public/pagos/${token}/confirmar`;
}

export function construirAprobacion(firma: string): AprobacionPublicaInput {
  return { firma: firma.trim() };
}

export function construirRechazo(motivo?: string | null): RechazoPublicoInput {
  const limpio = motivo?.trim();
  return limpio ? { motivo: limpio } : {};
}

export function getPresupuestoPublico(token: string): Promise<PresupuestoPublico> {
  return request<PresupuestoPublico>(rutaPresupuestoPublico(token));
}

export function aprobarPresupuestoPublico(
  token: string,
  firma: string,
): Promise<PresupuestoPublico> {
  return request<PresupuestoPublico>(rutaAprobarPresupuestoPublico(token), {
    method: "POST",
    body: JSON.stringify(construirAprobacion(firma)),
  });
}

export function rechazarPresupuestoPublico(
  token: string,
  motivo?: string | null,
): Promise<PresupuestoPublico> {
  return request<PresupuestoPublico>(rutaRechazarPresupuestoPublico(token), {
    method: "POST",
    body: JSON.stringify(construirRechazo(motivo)),
  });
}

export function getPagoPublico(token: string): Promise<PagoPublico> {
  return request<PagoPublico>(rutaPagoPublico(token));
}

export function confirmarPagoPublico(token: string): Promise<PagoPublico> {
  return request<PagoPublico>(rutaConfirmarPagoPublico(token), { method: "POST" });
}
