// Lógica pura de presentación del portal público (C-18, D7/R10).
// Vive en un módulo `.ts` sin JSX para poder cubrirla con `node --test`, que no
// procesa JSX; los componentes `.tsx` solo la conectan a la vista. Mismo patrón
// que `features/reserva-publica/retencion.ts` y `features/agenda/semanaUtils.ts`.
import { formatArs } from "../../shared/utils/format.ts";
import type { PagoPublico, PresupuestoPublico } from "../../shared/api/public";

// R2: marca única y fija del consultorio; sin slug, tenant ni selector de sucursal.
export interface MarcaConsultorio {
  nombre: string;
}

export const NOMBRE_CONSULTORIO = "Consultorio Odontológico";

export function marcaConsultorio(): MarcaConsultorio {
  return { nombre: NOMBRE_CONSULTORIO };
}

// R10: montos siempre en pesos argentinos.
export function totalEnArs(total: number): string {
  return formatArs(total);
}

export function montoEnArs(monto: number): string {
  return formatArs(monto);
}

// --- Presupuesto ------------------------------------------------------------

const ESTADOS_PRESUPUESTO: Record<string, string> = {
  borrador: "Borrador",
  enviado: "Enviado",
  aprobado: "Aprobado",
  rechazado: "Rechazado",
  cobrado: "Cobrado",
};

export function estadoPresupuestoLegible(estado: string): string {
  return ESTADOS_PRESUPUESTO[estado] ?? estado;
}

// D5: solo un presupuesto `enviado` admite aprobar/rechazar desde el portal.
export function puedeAprobar(estado: string): boolean {
  return estado === "enviado";
}

export function puedeRechazar(estado: string): boolean {
  return estado === "enviado";
}

export interface VistaPresupuesto {
  totalTexto: string;
  estadoTexto: string;
  puedeAprobar: boolean;
  puedeRechazar: boolean;
}

export function vistaPresupuesto(presupuesto: PresupuestoPublico): VistaPresupuesto {
  return {
    totalTexto: totalEnArs(presupuesto.total),
    estadoTexto: estadoPresupuestoLegible(presupuesto.estado),
    puedeAprobar: puedeAprobar(presupuesto.estado),
    puedeRechazar: puedeRechazar(presupuesto.estado),
  };
}

// La firma simple es el nombre del paciente; en blanco no habilita el envío.
export function puedeEnviarFirma(firma: string): boolean {
  return firma.trim().length > 0;
}

// --- Pago simulado ----------------------------------------------------------

const ESTADOS_PAGO: Record<string, string> = {
  pendiente: "Pendiente",
  aprobado: "Aprobado",
  rechazado: "Rechazado",
};

export function estadoPagoLegible(estado: string): string {
  return ESTADOS_PAGO[estado] ?? estado;
}

// Idempotencia de UI: el botón se deshabilita mientras la request está en curso
// (`confirmando`) y deja de ofrecerse cuando el pago ya está aprobado.
export function puedeConfirmarPago(pago: PagoPublico, confirmando: boolean): boolean {
  return pago.estado === "pendiente" && !confirmando;
}

export interface ResultadoPago {
  aprobado: boolean;
  rechazado: boolean;
  texto: string;
}

export function resultadoPago(pago: PagoPublico): ResultadoPago {
  if (pago.estado === "aprobado") {
    return {
      aprobado: true,
      rechazado: false,
      texto: `¡Listo! Registramos tu pago de ${montoEnArs(pago.monto)}.`,
    };
  }
  if (pago.estado === "rechazado") {
    return {
      aprobado: false,
      rechazado: true,
      texto: "El pago fue rechazado. Podés intentar de nuevo o comunicarte con el consultorio.",
    };
  }
  return {
    aprobado: false,
    rechazado: false,
    texto: `Tenés un pago pendiente de ${montoEnArs(pago.monto)}.`,
  };
}

// --- Errores (forma única {error:{code,message}}) ---------------------------

export const MENSAJE_NO_ENCONTRADO =
  "No encontramos este presupuesto. Verificá el enlace o pedí uno nuevo.";

export const MENSAJE_NO_DISPONIBLE =
  "Este pago todavía no está disponible. Aprobá primero el presupuesto.";

function tieneStatus(error: unknown, status: number): boolean {
  return (
    typeof error === "object" &&
    error !== null &&
    "status" in error &&
    (error as { status?: unknown }).status === status
  );
}

export function esErrorNoEncontrado(error: unknown): boolean {
  return tieneStatus(error, 404);
}

export function esErrorConflicto(error: unknown): boolean {
  return tieneStatus(error, 409);
}
