// Helpers puros de la vista semanal (C-09b, D5): semana lunes–domingo en ART.
// Sin estado ni acceso a red: la página los consume con `useMemo`.
import type { TurnoOut } from "../../shared/api/agenda";
import type { Sillon } from "./types";
import { toIsoDate } from "../../shared/date.ts";

const MS_POR_DIA = 86_400_000;

const FORMATO_NOMBRE_DIA = new Intl.DateTimeFormat("es-AR", {
  weekday: "short",
  timeZone: "UTC",
});
const FORMATO_DIA = new Intl.DateTimeFormat("es-AR", { day: "numeric", timeZone: "UTC" });
const FORMATO_MES_CORTO = new Intl.DateTimeFormat("es-AR", { month: "short", timeZone: "UTC" });
const FORMATO_MES_LARGO = new Intl.DateTimeFormat("es-AR", { month: "long", timeZone: "UTC" });
const FORMATO_DIA_SEMANA = new Intl.DateTimeFormat("es-AR", {
  weekday: "long",
  timeZone: "UTC",
});
const FORMATO_ANIO = new Intl.DateTimeFormat("es-AR", { year: "numeric", timeZone: "UTC" });

export interface DiaSemana {
  /** Día de calendario ART en formato `YYYY-MM-DD`. */
  iso: string;
  /** Nombre corto es-AR: `lun`, `mar`, … */
  nombre: string;
  /** Día del mes sin ceros a la izquierda. */
  dia: number;
  /** Mes corto es-AR: `nov`, `dic`, … */
  mes: string;
}

export interface CeldaSemana {
  sillonId: string;
  fecha: string;
  turnos: TurnoOut[];
}

/** Clave estable de una celda: `sillonId|YYYY-MM-DD`. */
export function claveCelda(sillonId: string, fecha: string): string {
  return `${sillonId}|${fecha}`;
}

/** Interpreta un día de calendario o un instante ISO como día ART (`YYYY-MM-DD`). */
function isoDeEntrada(valor: string | Date): string {
  if (typeof valor === "string" && /^\d{4}-\d{2}-\d{2}$/.test(valor)) {
    return valor;
  }
  return toIsoDate(new Date(valor));
}

function aInstanteMedianocheUtc(iso: string): Date {
  return new Date(`${iso}T00:00:00Z`);
}

function aIso(fecha: Date): string {
  return fecha.toISOString().slice(0, 10);
}

/** Suma días de calendario sin arrastrar la zona del navegador. */
export function sumarDias(iso: string, dias: number): string {
  return aIso(new Date(aInstanteMedianocheUtc(iso).getTime() + dias * MS_POR_DIA));
}

/**
 * Lunes (ART) de la semana que contiene la fecha o el instante indicado.
 * Acepta `YYYY-MM-DD` o un ISO completo; un domingo pertenece a la semana que
 * empezó el lunes anterior (D5).
 */
export function inicioSemana(valor: string | Date): string {
  const iso = isoDeEntrada(valor);
  const diaDeSemana = aInstanteMedianocheUtc(iso).getUTCDay(); // 0 = domingo
  const desplazamiento = (diaDeSemana + 6) % 7; // lunes = 0
  return sumarDias(iso, -desplazamiento);
}

/** Los siete días de la semana, de lunes a domingo, con etiquetas es-AR. */
export function diasSemana(lunes: string): DiaSemana[] {
  return Array.from({ length: 7 }, (_, indice) => {
    const iso = sumarDias(lunes, indice);
    const fecha = aInstanteMedianocheUtc(iso);
    return {
      iso,
      nombre: FORMATO_NOMBRE_DIA.format(fecha),
      dia: Number(FORMATO_DIA.format(fecha)),
      mes: FORMATO_MES_CORTO.format(fecha),
    };
  });
}

/** Rango inclusivo que consume `GET /api/v1/turnos`. */
export function rangoSemana(lunes: string): { desde: string; hasta: string } {
  return { desde: lunes, hasta: sumarDias(lunes, 6) };
}

/**
 * Título de la semana en español rioplatense (R10):
 * `lunes 2 – domingo 8 de noviembre de 2026`. Nombra los dos meses cuando la
 * semana cruza el límite de mes o de año.
 */
export function formatearRangoSemana(lunes: string): string {
  const domingo = sumarDias(lunes, 6);
  const inicio = aInstanteMedianocheUtc(lunes);
  const fin = aInstanteMedianocheUtc(domingo);
  const cruzaMes = inicio.getUTCMonth() !== fin.getUTCMonth();
  const desde = `${FORMATO_DIA_SEMANA.format(inicio)} ${FORMATO_DIA.format(inicio)}${
    cruzaMes ? ` de ${FORMATO_MES_LARGO.format(inicio)}` : ""
  }`;
  const hasta = `${FORMATO_DIA_SEMANA.format(fin)} ${FORMATO_DIA.format(fin)} de ${FORMATO_MES_LARGO.format(
    fin,
  )} de ${FORMATO_ANIO.format(fin)}`;
  return `${desde} – ${hasta}`;
}

/** Orden estable dentro de una celda: hora de inicio y, a igualdad, `id`. */
function ordenarPorInicio(turnos: TurnoOut[]): TurnoOut[] {
  return [...turnos].sort((a, b) => {
    const inicioA = Date.parse(a.inicio);
    const inicioB = Date.parse(b.inicio);
    if (inicioA !== inicioB) return inicioA - inicioB;
    return a.id.localeCompare(b.id);
  });
}

/** Turnos que caen dentro de la semana mostrada (descarta los reprogramados fuera). */
export function turnosDeSemana(turnos: TurnoOut[], lunes: string): TurnoOut[] {
  const fechas = new Set(diasSemana(lunes).map((dia) => dia.iso));
  return turnos.filter((turno) => fechas.has(toIsoDate(new Date(turno.inicio))));
}

/**
 * Agrupa los turnos de la semana por sillón y día ART. Descarta los turnos
 * fuera del rango mostrado (por ejemplo, tras reprogramar a otra semana).
 */
export function agruparSemana(turnos: TurnoOut[], lunes: string): Record<string, TurnoOut[]> {
  const fechas = new Set(diasSemana(lunes).map((dia) => dia.iso));
  const grupos: Record<string, TurnoOut[]> = {};
  for (const turno of turnos) {
    const fecha = toIsoDate(new Date(turno.inicio));
    if (!fechas.has(fecha)) continue;
    const clave = claveCelda(turno.sillon_id, fecha);
    grupos[clave] = [...(grupos[clave] ?? []), turno];
  }
  for (const clave of Object.keys(grupos)) {
    grupos[clave] = ordenarPorInicio(grupos[clave]);
  }
  return grupos;
}

/** Los siete días de un sillón, en orden, con sus turnos ordenados por hora. */
export function filaSemana(turnos: TurnoOut[], lunes: string, sillon: Sillon): TurnoOut[][] {
  const grupos = agruparSemana(
    turnos.filter((turno) => turno.sillon_id === sillon.id),
    lunes,
  );
  return diasSemana(lunes).map((dia) => grupos[claveCelda(sillon.id, dia.iso)] ?? []);
}

/**
 * Celdas de la grilla en orden sillón → día, solo con sillones activos (D6).
 * Siempre son `sillonesActivos × 7` celdas, aunque no haya turnos.
 */
export function construirCeldas(
  turnos: TurnoOut[],
  lunes: string,
  sillones: Sillon[],
): CeldaSemana[] {
  const grupos = agruparSemana(turnos, lunes);
  const dias = diasSemana(lunes);
  return sillones
    .filter((sillon) => sillon.activo)
    .flatMap((sillon) =>
      dias.map((dia) => ({
        sillonId: sillon.id,
        fecha: dia.iso,
        turnos: grupos[claveCelda(sillon.id, dia.iso)] ?? [],
      })),
    );
}

/** Filtro por profesional en cliente (D7): `null` = “Todos los profesionales”. */
export function filtrarPorProfesional(
  turnos: TurnoOut[],
  profesionalId: string | null,
): TurnoOut[] {
  if (profesionalId === null) return turnos;
  return turnos.filter((turno) => turno.profesional_id === profesionalId);
}
