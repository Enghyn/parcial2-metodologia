// Helpers puros de rate-limit para la SPA (C-10, D12).
export function parseRetryAfter(value: string | null): number | null {
  if (value === null) return null;
  const trimmed = value.trim();
  if (trimmed === "") return null;
  const n = Number(trimmed);
  if (!Number.isFinite(n)) return null;
  const intVal = Math.trunc(n);
  if (intVal < 0) return null;
  return intVal;
}

export function mensajeRateLimit(segundos: number): string {
  if (segundos <= 0) {
    return "Demasiadas requests. Intentá de nuevo en unos instantes.";
  }
  if (segundos === 1) {
    return "Demasiadas requests. Intentá de nuevo en 1 segundo.";
  }
  return `Demasiadas requests. Intentá de nuevo en ${segundos} segundos.`;
}