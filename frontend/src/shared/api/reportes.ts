// Cliente tipado de reportes de gestión (C-21).
import { request, requestText } from "./client";

export type EstadoTurno =
  | "reservado"
  | "confirmado"
  | "presente"
  | "atendido"
  | "cancelado"
  | "ausente";

export type MedioPago = "efectivo" | "transferencia" | "debito" | "credito" | "otro";

export interface OcupacionRecurso {
  id: string;
  nombre: string;
  reservado: number;
  confirmado: number;
  presente: number;
  atendido: number;
  cancelado: number;
  tasa_ocupacion: number;
  horas_bloqueadas: number;
}

export interface OcupacionReporte {
  desde: string;
  hasta: string;
  sillones: OcupacionRecurso[];
  profesionales: OcupacionRecurso[];
}

export interface FacturacionMedio {
  medio_pago: string;
  total: string;
}

export interface FacturacionOS {
  obra_social: string;
  monto_os: string;
  copago_paciente: string;
  total_paciente: string;
}

export interface FacturacionReporte {
  desde: string;
  hasta: string;
  por_medio_pago: FacturacionMedio[];
  total_ingresos: string;
  balance_neto: string;
  por_obra_social: FacturacionOS[];
}

export interface AusentismoReporte {
  desde: string;
  hasta: string;
  cancelados: number;
  no_presentados: number;
  recuperados: number;
  tasa_ausentismo: number;
  total_turnos: number;
}

function conRango(
  path: string,
  desde?: string,
  hasta?: string,
  profesionalId?: string | null,
  sillonId?: string | null,
): string {
  const params = new URLSearchParams();
  if (desde !== undefined && desde !== "") params.set("desde", desde);
  if (hasta !== undefined && hasta !== "") params.set("hasta", hasta);
  if (profesionalId !== undefined && profesionalId !== null && profesionalId !== "")
    params.set("profesional_id", profesionalId);
  if (sillonId !== undefined && sillonId !== null && sillonId !== "")
    params.set("sillon_id", sillonId);
  const qs = params.toString();
  return qs ? `${path}?${qs}` : path;
}

export function reporteOcupacion(
  desde?: string,
  hasta?: string,
  profesionalId?: string | null,
  sillonId?: string | null,
): Promise<OcupacionReporte> {
  return request<OcupacionReporte>(
    conRango("/api/v1/reportes/ocupacion", desde, hasta, profesionalId, sillonId),
  );
}

export function exportarOcupacionCsv(
  desde?: string,
  hasta?: string,
  profesionalId?: string | null,
  sillonId?: string | null,
): Promise<string> {
  return requestText(
    conRango("/api/v1/reportes/ocupacion/export.csv", desde, hasta, profesionalId, sillonId),
    { headers: { Accept: "text/csv" } },
  );
}

export function reporteFacturacion(desde?: string, hasta?: string): Promise<FacturacionReporte> {
  return request<FacturacionReporte>(conRango("/api/v1/reportes/facturacion", desde, hasta));
}

export function exportarFacturacionCsv(desde?: string, hasta?: string): Promise<string> {
  return requestText(
    conRango("/api/v1/reportes/facturacion/export.csv", desde, hasta),
    { headers: { Accept: "text/csv" } },
  );
}

export function reporteAusentismo(desde?: string, hasta?: string): Promise<AusentismoReporte> {
  return request<AusentismoReporte>(conRango("/api/v1/reportes/ausentismo", desde, hasta));
}

export function exportarAusentismoCsv(desde?: string, hasta?: string): Promise<string> {
  return requestText(
    conRango("/api/v1/reportes/ausentismo/export.csv", desde, hasta),
    { headers: { Accept: "text/csv" } },
  );
}

export interface DescargaCSV {
  nombre: string;
  contenido: string;
  tipo: "text/csv";
}

export function descargarCsv(contenido: string, nombre: string): void {
  const blob = new Blob([contenido], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = nombre;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
