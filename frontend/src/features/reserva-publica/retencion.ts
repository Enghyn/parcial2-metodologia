// Helpers puros de retención/cuenta regresiva (C-10, D12).
export function segundosRestantes(expiraEn: string | number | Date, ahoraMs: number): number {
  const expiraMs = expiraEn instanceof Date ? expiraEn.getTime() : new Date(expiraEn).getTime();
  const diff = expiraMs - ahoraMs;
  if (!Number.isFinite(diff) || diff <= 0) return 0;
  return Math.floor(diff / 1000);
}

export function formatearCuentaRegresiva(segundos: number): string {
  const s = Math.max(0, Math.floor(segundos));
  const min = Math.floor(s / 60);
  const sec = s % 60;
  return `${String(min).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
}

export function retencionVencida(expiraEn: string | number | Date, ahoraMs: number): boolean {
  const expiraMs = expiraEn instanceof Date ? expiraEn.getTime() : new Date(expiraEn).getTime();
  return expiraMs <= ahoraMs;
}