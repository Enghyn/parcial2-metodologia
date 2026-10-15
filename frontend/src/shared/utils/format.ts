// Utilidades de formato: ARS + textos (R10: rioplatense y pesos en superficies públicas).

export function formatArs(monto: number): string {
  return new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS" }).format(monto);
}
