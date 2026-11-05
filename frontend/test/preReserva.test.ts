import assert from "node:assert/strict";
import { test } from "node:test";

import { formatearCuentaRegresiva, retencionVencida, segundosRestantes } from "../src/features/reserva-publica/retencion.ts";

test("segundosRestantes positivo, cero, negativo", () => {
  const expira = 10_000;
  assert.equal(segundosRestantes(expira, 0), 10);
  assert.equal(segundosRestantes(expira, 10_000), 0);
  assert.equal(segundosRestantes(expira, 15_000), 0);
});

test("formatearCuentaRegresiva", () => {
  assert.equal(formatearCuentaRegresiva(599), "09:59");
  assert.equal(formatearCuentaRegresiva(5), "00:05");
  assert.equal(formatearCuentaRegresiva(0), "00:00");
});

test("retencionVencida", () => {
  assert.equal(retencionVencida(5_000, 10_000), true);
  assert.equal(retencionVencida(10_000, 10_000), true);
  assert.equal(retencionVencida(15_000, 10_000), false);
});