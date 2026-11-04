// Helpers puros de fecha. Zona canónica del consultorio: America/Argentina/Buenos_Aires.
export const TZ_CONSULTORIO = "America/Argentina/Buenos_Aires";

export function toIsoDate(date: Date): string {
  const partes = new Intl.DateTimeFormat("en-CA", {
    timeZone: TZ_CONSULTORIO,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);
  const valor = (tipo: string): string => partes.find((parte) => parte.type === tipo)?.value ?? "";
  return `${valor("year")}-${valor("month")}-${valor("day")}`;
}

export function addDays(date: Date, days: number): Date {
  const result = new Date(date.getTime());
  result.setDate(result.getDate() + days);
  return result;
}

export function formatHora(iso: string): string {
  return new Date(iso).toLocaleTimeString("es-AR", {
    timeZone: TZ_CONSULTORIO,
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatFecha(iso: string): string {
  return new Date(iso).toLocaleDateString("es-AR", {
    timeZone: TZ_CONSULTORIO,
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

// El input datetime-local llega como hora de pared ART (UTC-3, sin DST).
export function localInputToUtc(value: string): string {
  const normalizado = value.length === 16 ? `${value}:00` : value;
  return new Date(`${normalizado}-03:00`).toISOString();
}

export function hoy(): Date {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  return d;
}
