// Constructor puro del enlace Click-to-Chat (RN-G-01).
export function construirUrlWhatsapp(telefono: string, mensaje: string): string {
  const numero = telefono.replace(/\D/g, "");
  if (numero === "") {
    return "";
  }
  return `https://wa.me/${numero}?text=${encodeURIComponent(mensaje)}`;
}
