// Cliente tipado de caja (C-08 + C-12).
import { request, requestText } from "./client";

export type TipoMovimiento = "ingreso" | "egreso";
export type MedioPago = "efectivo" | "transferencia" | "debito" | "credito" | "otro";
export type EstadoCierre = "pendiente" | "cerrado" | "reabierto";

export interface Movimiento {
  id: string;
  fecha: string;
  tipo: TipoMovimiento;
  medio_pago: MedioPago;
  monto: string;
  concepto: string;
  turno_id: string | null;
  usuario_id: string;
}

export interface MovimientoInput {
  tipo: TipoMovimiento;
  medio_pago: MedioPago;
  monto: string;
  concepto: string;
  turno_id?: string | null;
}

export interface ResumenDiario {
  fecha: string;
  total_ingresos: string;
  total_egresos: string;
  balance: string;
  por_medio_pago: Record<string, string>;
}

export interface Cierre {
  id: string;
  fecha_dia: string;
  estado: EstadoCierre;
  balance: string;
  total_ingresos: string;
  total_egresos: string;
  aprobado_por: string | null;
  aprobado_en: string | null;
  created_at: string;
}

export interface CierreInput {
  fecha_dia?: string;
}

export interface MovimientoCuentaCorriente {
  id: string;
  fecha: string;
  tipo: TipoMovimiento;
  medio_pago: MedioPago;
  monto: string;
  concepto: string;
  usuario_id: string;
}

export interface CuentaCorriente {
  paciente_id: string;
  saldo: string;
  detalle: MovimientoCuentaCorriente[];
}

export interface CuentaCorrienteResumen {
  paciente_id: string;
  nombre: string;
  saldo: string;
}

export interface AjusteInput {
  movimiento_corregido_id: string;
  motivo: string;
  tipo: TipoMovimiento;
  medio_pago: MedioPago;
  monto: string;
  concepto: string;
  turno_id?: string | null;
}

export interface Ajuste {
  id: string;
  movimiento_corregido_id: string;
  movimiento_ajuste_id: string;
  motivo: string;
  fecha: string;
  usuario_aprobador_id: string;
  created_at: string;
}

function conFecha(path: string, fecha?: string): string {
  if (fecha === undefined || fecha === "") return path;
  return `${path}?fecha=${encodeURIComponent(fecha)}`;
}

export function listarMovimientos(fecha?: string): Promise<Movimiento[]> {
  return request<Movimiento[]>(conFecha("/api/v1/caja/movimientos", fecha));
}

export function crearMovimiento(input: MovimientoInput): Promise<Movimiento> {
  return request<Movimiento>("/api/v1/caja/movimientos", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function resumenDiario(fecha?: string): Promise<ResumenDiario> {
  return request<ResumenDiario>(conFecha("/api/v1/caja/resumen-diario", fecha));
}

// --- C-12: Cierre diario ---

export function cerrarCaja(input: CierreInput): Promise<Cierre> {
  return request<Cierre>("/api/v1/caja/cierres", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function listarCierres(): Promise<Cierre[]> {
  return request<Cierre[]>("/api/v1/caja/cierres");
}

// --- C-12: Cuenta corriente por paciente ---

export function cuentaCorriente(pacienteId: string): Promise<CuentaCorriente> {
  return request<CuentaCorriente>(`/api/v1/caja/cuenta-corriente/${encodeURIComponent(pacienteId)}`);
}

export function cuentasCorrientes(): Promise<CuentaCorrienteResumen[]> {
  return request<CuentaCorrienteResumen[]>("/api/v1/caja/cuentas-corrientes");
}

// --- C-12: Ajustes auditados ---

export function registrarAjuste(input: AjusteInput): Promise<Ajuste> {
  return request<Ajuste>("/api/v1/caja/ajustes", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

// --- C-12: Export CSV ---

export function exportCajaCsv(fecha?: string): Promise<string> {
  return requestText(conFecha("/api/v1/caja/export", fecha), {
    headers: { Accept: "text/csv" },
  });
}
