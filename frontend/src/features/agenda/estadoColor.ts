// Mapa puro estado -> clases Tailwind (D5). Sin `any`.
import type { EstadoTurno } from "../../shared/api/agenda";

export function estadoClasses(estado: EstadoTurno): string {
  switch (estado) {
    case "reservado":
      return "border-sky-300 bg-sky-50 text-sky-900";
    case "confirmado":
      return "border-blue-400 bg-blue-50 text-blue-900";
    case "presente":
      return "border-amber-400 bg-amber-50 text-amber-900";
    case "atendido":
      return "border-emerald-400 bg-emerald-50 text-emerald-900";
    case "cancelado":
      return "border-rose-300 bg-rose-50 text-rose-900 line-through opacity-60";
    case "ausente":
      return "border-slate-400 bg-slate-100 text-slate-700";
    default:
      return "border-border bg-background text-foreground";
  }
}