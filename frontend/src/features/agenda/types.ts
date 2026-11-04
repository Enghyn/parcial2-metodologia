// Tipos del feature agenda (sin `any`, R7).
import type { EstadoTurno, TurnoOut } from "../../shared/api/agenda";

export interface Sillon {
  id: string;
  nombre: string;
  activo: boolean;
}

export interface Profesional {
  id: string;
  nombre: string;
}

export interface Paciente {
  id: string;
  nombre: string;
}

export interface Catalogos {
  sillones: Sillon[];
  profesionales: Profesional[];
  pacientes: Paciente[];
}

export type TurnoView = TurnoOut;

export type { EstadoTurno };