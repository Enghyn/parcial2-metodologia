import assert from "node:assert/strict";
import { test } from "node:test";

import { construirPreReserva, rutaQrReserva, rutaQrTurno } from "../src/shared/api/public.ts";

test("rutas QR", () => {
  assert.equal(rutaQrReserva(), "/api/v1/public/qr/reserva.svg");
  assert.equal(rutaQrTurno("abc"), "/api/v1/public/turnos/abc/qr.svg");
});

test("construirPreReserva sin paciente", () => {
  const out = construirPreReserva({
    prestacion: "Consulta",
    duracion_min: 30,
    inicio: "2027-01-01T10:00:00",
    profesional_id: "p",
    sillon_id: "s",
  });
  assert.equal((out as any).paciente, undefined);
});