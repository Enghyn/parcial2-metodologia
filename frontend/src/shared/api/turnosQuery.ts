// Query del listado de turnos (C-09b). Puro y sin dependencias de red: lo usan
// `listarTurnos` y los tests de `node:test` (que no pueden cargar el cliente React).

export interface FiltroTurnosQuery {
  fecha?: string;
  desde?: string;
  hasta?: string;
  profesional_id?: string;
  sillon_id?: string;
}

/**
 * Serializa los filtros de `GET /api/v1/turnos` en el orden canónico
 * `fecha, desde, hasta, profesional_id, sillon_id`. Devuelve solo la query
 * (sin `?`) y cadena vacía cuando no hay filtros.
 */
export function construirQueryTurnos(filtros: FiltroTurnosQuery): string {
  const params = new URLSearchParams();
  if (filtros.fecha !== undefined) params.set("fecha", filtros.fecha);
  if (filtros.desde !== undefined) params.set("desde", filtros.desde);
  if (filtros.hasta !== undefined) params.set("hasta", filtros.hasta);
  if (filtros.profesional_id !== undefined) params.set("profesional_id", filtros.profesional_id);
  if (filtros.sillon_id !== undefined) params.set("sillon_id", filtros.sillon_id);
  return params.toString();
}

/** Ruta completa del listado: `/api/v1/turnos` con o sin query. */
export function rutaTurnos(filtros: FiltroTurnosQuery): string {
  const query = construirQueryTurnos(filtros);
  return query.length > 0 ? `/api/v1/turnos?${query}` : "/api/v1/turnos";
}
