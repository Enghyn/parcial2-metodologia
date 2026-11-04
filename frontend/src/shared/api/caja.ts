// Cliente tipado de caja (C-08).
import { request } from "./client";

export type TipoMovimiento = "ingreso" | "egreso";
export type MedioPago = "efectivo" | "transferencia" | "debito" | "credito" | "otro";

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
