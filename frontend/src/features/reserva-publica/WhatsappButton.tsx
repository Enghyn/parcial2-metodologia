// Botón Click-to-Chat de WhatsApp con mensaje prearmado (RN-G-01, R10).
import type { ReactElement } from "react";
import type { TurnoPublicoOut } from "../../shared/api/public";
import { formatFecha, formatHora } from "./types";

interface WhatsappButtonProps {
  turno: TurnoPublicoOut;
}

export function WhatsappButton({ turno }: WhatsappButtonProps): ReactElement {
  const telefono = String(import.meta.env.VITE_WHATSAPP_CONSULTORIO ?? "").replace(/\D/g, "");
  const mensaje = encodeURIComponent(
    `Hola, confirmo mi turno de ${turno.prestacion} el ${formatFecha(
      turno.inicio,
    )} a las ${formatHora(turno.inicio)} con ${turno.profesional_nombre}.`,
  );

  if (telefono === "") {
    return (
      <button
        type="button"
        disabled
        title="Falta configurar el WhatsApp del consultorio"
        className="rounded bg-emerald-600 px-4 py-2 text-white opacity-60"
      >
        Enviar aviso por WhatsApp
      </button>
    );
  }

  return (
    <a
      href={`https://wa.me/${telefono}?text=${mensaje}`}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-block rounded bg-emerald-600 px-4 py-2 text-white"
    >
      Enviar aviso por WhatsApp
    </a>
  );
}
